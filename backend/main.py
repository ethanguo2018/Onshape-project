import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# .env lives in hidden/ at the repo root; load it once at startup.
# ANTHROPIC_API_KEY is available via os.getenv() but is never logged or printed.
load_dotenv(Path(__file__).parent.parent / "hidden" / ".env")

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
