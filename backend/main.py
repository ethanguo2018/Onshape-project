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
