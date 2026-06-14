import os
import json
from pathlib import Path
from fastapi import FastAPI
import anthropic
import jsonschema
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# .env lives in hidden/ at the repo root; load it once at startup.
# ANTHROPIC_API_KEY is available via os.getenv() but is never logged or printed.
load_dotenv(Path(__file__).parent.parent / "hidden" / ".env")

# Load gusset schema once at startup for use in /parse-test.
_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "gusset.schema.json"
with open(_SCHEMA_PATH) as _f:
    GUSSET_SCHEMA = json.load(_f)

# Load all available part schemas for the conversational parser.
_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
PART_SCHEMAS: dict[str, dict] = {}
for _schema_file in _SCHEMAS_DIR.glob("*.schema.json"):
    _part_type = _schema_file.stem.replace(".schema", "")
    with open(_schema_file) as _f:
        PART_SCHEMAS[_part_type] = json.load(_f)

app = FastAPI(title="FRC Text-to-CAD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5500",   # VS Code Live Server
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",                    # file:// origin (opening index.html directly)
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    echo: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest):
    # ---------------------------------------------------------------
    # TODO: Replace this echo with the real Claude API call, e.g.:
    #
    #   import anthropic
    #   client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    #   message = client.messages.create(
    #       model="claude-sonnet-4-6",
    #       max_tokens=1024,
    #       messages=[{"role": "user", "content": req.text}],
    #   )
    #   parsed_json = message.content[0].text
    #   return ParseResponse(echo=parsed_json)
    # ---------------------------------------------------------------
    return ParseResponse(echo=req.text)


# TEMPORARY — remove once the real parser is wired in
@app.post("/parse-test")
def parse_test(req: ParseRequest):
    # ------------------------------------------------------------------
    # PLACEHOLDER SYSTEM PROMPT — replace with Peter's real parser prompt
    # before production use. This prompt is intentionally minimal; it
    # just proves the schema-based parse pipeline works end to end.
    # ------------------------------------------------------------------
    system_prompt = """You parse FRC part descriptions into structured JSON order forms.

Output ONLY a raw JSON object — no markdown, no code fences, no explanation.
All fields are required. Use exactly these field names and allowed values:

  part_type      : string, always "gusset"
  tube_size_a    : string, one of ["2x1", "1x1"]
  tube_size_b    : string, one of ["2x1", "1x1"]
  angle_deg      : number, between 30 and 150
  holes_per_side : integer, between 1 and 6
  hole_spec      : string, always "#10"
  hole_pattern   : string, one of ["maxtube_grid", "even_spacing"]
  thickness_in   : number, one of [0.090, 0.125, 0.190]
  pocketed       : boolean

If a field is not mentioned, choose the most reasonable default."""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": req.text}],
        )
        raw = message.content[0].text.strip()

        try:
            order_form = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"JSON parse failed: {e}", "raw": raw}

        try:
            jsonschema.validate(instance=order_form, schema=GUSSET_SCHEMA)
        except jsonschema.ValidationError as e:
            return {"valid": False, "error": f"Schema validation failed: {e.message}", "raw": raw}

        return {"valid": True, "order_form": order_form}

    except Exception as e:
        return {"valid": False, "error": str(e), "raw": ""}


# --- Conversational parser ---

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatParseRequest(BaseModel):
    messages: list[ChatMessage]


def _build_schema_summary(schemas: dict[str, dict]) -> str:
    """Render each loaded schema as a compact field list for the system prompt."""
    lines = []
    for part_type, schema in schemas.items():
        lines.append(f"## {part_type}")
        props = schema.get("properties", {})
        for field, spec in props.items():
            hints = []
            if "enum" in spec:
                hints.append(f"one of {spec['enum']}")
            elif "const" in spec:
                hints.append(f'always "{spec["const"]}"')
            else:
                if "minimum" in spec or "maximum" in spec:
                    lo = spec.get("minimum", "?")
                    hi = spec.get("maximum", "?")
                    hints.append(f"number {lo}–{hi}")
                if spec.get("type"):
                    hints.append(spec["type"])
            desc = spec.get("description", "")
            hint_str = f" ({', '.join(hints)})" if hints else ""
            lines.append(f"  - {field}{hint_str}: {desc}")
        lines.append("")
    return "\n".join(lines)


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    # Strip markdown code fences (```json, ```, any language tag)
    if text.startswith("```"):
        first_newline = text.find("\n")
        text = text[first_newline + 1:] if first_newline != -1 else text[3:]
        last_fence = text.rfind("```")
        if last_fence != -1:
            text = text[:last_fence]
        text = text.strip()
    # Extract from first { to matching last } to skip surrounding prose
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end >= start:
        text = text[start:end + 1]
    return json.loads(text)


# PLACEHOLDER SYSTEM PROMPT — replace with Peter+Ethan's real prompt before production.
_CHAT_SYSTEM_PROMPT_TEMPLATE = """\
# PLACEHOLDER SYSTEM PROMPT — pending Peter+Ethan's real prompt.

You are an FRC part order assistant. Gather all required information to produce a \
complete, valid order form for an FRC robot part.

Supported part types: {part_types}

{schema_summary}
Instructions:
1. First identify the part type from the conversation. If unclear, ask which part the \
user wants.
2. Once the part type is known, identify which required fields are still missing or \
ambiguous from the conversation so far.
3. If anything is missing, ambiguous, or out of scope, reply with ONE short clarifying \
question. Reference allowed values when relevant \
(e.g. "We support 2x1 or 1x1 tubes — which would you like for each arm?").
4. If and only if every required field is present and valid, output the complete order \
form.

CRITICAL: Output ONLY a raw JSON object — nothing else.
- Do NOT use markdown, backticks, or code fences of any kind
- Do NOT write any prose, explanation, or commentary before or after the JSON
- The very first character of your response must be {{ and the very last must be }}
- Any other output format will break the parser
Use exactly one of these two formats:

If information is still needed:
{{"status": "incomplete", "message": "<your single clarifying question>"}}

If all required fields are collected:
{{"status": "complete", "part_type": "<part_type>", "order_form": {{<all fields>}}}}
"""


@app.post("/chat-parse")
def chat_parse(req: ChatParseRequest):
    try:
        part_types = ", ".join(PART_SCHEMAS.keys()) if PART_SCHEMAS else "gusset"
        schema_summary = _build_schema_summary(PART_SCHEMAS)
        system_prompt = _CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            part_types=part_types,
            schema_summary=schema_summary,
        )

        convo = [{"role": m.role, "content": m.content} for m in req.messages]

        model_name = "claude-sonnet-4-6"
        max_tok = 1024
        print(f"[chat-parse] model={model_name} max_tokens={max_tok} messages={len(convo)}")
        for i, msg in enumerate(convo):
            preview = msg["content"][:80].replace("\n", "\\n")
            print(f"[chat-parse]   msg[{i}] role={msg['role']} content={repr(preview)}")

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tok,
            system=system_prompt,
            messages=convo,
        )

        raw = response.content[0].text

        print(f"[chat-parse] ===RAW START===\n{raw}\n[chat-parse] ===RAW END=== (repr: {repr(raw)})")
        try:
            parsed = _extract_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[chat-parse] JSON parse failed: {e}")
            return {"status": "error", "message": f"Could not parse Claude's response: {e}", "raw_response": raw}

        status = parsed.get("status")

        if status == "incomplete":
            return {"status": "incomplete", "message": parsed.get("message", "Could you clarify?")}

        if status == "complete":
            part_type = parsed.get("part_type", "")
            order_form = parsed.get("order_form", {})

            schema = PART_SCHEMAS.get(part_type)
            if schema is None:
                return {"status": "incomplete", "message": f"Part type '{part_type}' is not supported. Supported types: {list(PART_SCHEMAS.keys())}."}

            try:
                jsonschema.validate(instance=order_form, schema=schema)
            except jsonschema.ValidationError as e:
                return {"status": "incomplete", "message": f"The order form has an issue: {e.message}. Could you clarify?"}

            return {"status": "complete", "order_form": order_form}

        # Unexpected status value — treat as incomplete.
        return {"status": "incomplete", "message": parsed.get("message", "Could you tell me more about what you need?")}

    except Exception as e:
        import traceback
        print(f"[chat-parse] EXCEPTION {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": f"{type(e).__name__}: {e}"}


# TEMPORARY — remove once the real parser is wired in
@app.get("/test-claude")
def test_claude():
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say hello and confirm you are working in one short sentence.",
            }],
        )
        return {"reply": message.content[0].text}
    except Exception as e:
        return {"error": str(e)}
