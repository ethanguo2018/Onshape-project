# FRC Text-to-CAD Tool

## Project Overview

An educational tool for FRC students to convert plain English part descriptions into parametric CAD geometry for FIRST Robotics competition designs.

## Architecture

```
Student Input (Plain English)
    ↓
Frontend (Static HTML/CSS/JS)
    ↓
Backend (Claude API - Parsing only)
    ↓
Deterministic Templates (CAD Geometry Generation)
    ↓
CAD Output
```

1. **Frontend**: Student enters plain English part description
2. **Backend**: Python processes description via Claude API, outputs JSON order form
3. **Validator**: Checks JSON structure and constraints
4. **Template Engine**: Generates parametric CAD geometry from validated order

## Key Principles

- **AI handles language only**: Claude parses the student's description into a structured JSON order form
- **Deterministic templates generate geometry**: No AI-generated CAD code; all geometry comes from parameterized templates
- **Validation**: Backend validates the parsed JSON against allowed part types and parameters before passing to templates

## Tech Stack
- Frontend: Plain HTML/CSS/JavaScript (no frameworks)
- Backend: Python with Claude API
- Data: JSON order forms

## Current Phase

**Conversational Parser** — Multi-turn chat loop that gathers all required fields before producing a validated order form.

### Backend endpoints (`backend/main.py`)
| Endpoint | Purpose | Status |
|---|---|---|
| `GET /health` | Health check | stable |
| `POST /parse` | Echo stub (no Claude call yet) | placeholder |
| `POST /parse-test` | One-shot Claude parse + schema validation | working |
| `GET /test-claude` | Connectivity check | working |
| `POST /chat-parse` | **Conversational parser** — stateless; accepts full message history each turn | **new** |

### `/chat-parse` design
- **Stateless**: frontend sends the entire `messages` array each turn; backend holds no session state.
- Request: `{"messages": [{"role": "user"|"assistant", "content": "..."}]}`
- Claude is instructed (via system prompt) to output raw JSON in one of two shapes:
  - `{"status": "incomplete", "message": "<clarifying question>"}` — missing fields remain
  - `{"status": "complete", "part_type": "...", "order_form": {...}}` — all fields present
- Backend validates `order_form` against the matching schema in `schemas/` via `jsonschema`. Validation failure loops back as `"incomplete"`.
- System prompt is marked **PLACEHOLDER** — pending Peter+Ethan's real prompt.

### Frontend pages
| File | Purpose |
|---|---|
| `frontend/index.html` | Original one-shot input UI (unchanged) |
| `frontend/chat.html` | **New** multi-turn chat UI |

`frontend/chat.html` maintains `conversation[]` in JS, appends each turn, and posts the full array to `/chat-parse`. When `status === "complete"` it renders the order form JSON in a green card and locks the input.

## Example Conversational Flow

1. Student types: "I need a gusset"
2. Claude asks: "What tube sizes for each arm — 2x1 or 1x1?"
3. Student answers → Claude asks next missing field
4. After all fields collected → backend validates against `gusset.schema.json`
5. Green "Order form complete" card shown with final JSON

## Order Form Schemas

JSON Schemas live in `schemas/`. Each file defines the contract the Claude parser must fill and the validator must check before geometry generation.

- `schemas/gusset.schema.json` — JSON Schema draft 2020-12 for gusset order forms
- `schemas/gusset.example.json` — one valid filled-in example

`PART_SCHEMAS` is loaded at startup by globbing `schemas/*.schema.json`, so adding `motor_plate.schema.json` or `gearbox_plate.schema.json` automatically makes them available to `/chat-parse`.

**Note:** enum values and numeric bounds are placeholders pending Peter's review.

## Running Locally

```bash
# from repo root
.venv/bin/uvicorn backend.main:app --reload
# then open frontend/chat.html directly in browser
```

## Next Steps
- Replace placeholder system prompt with Peter+Ethan's real prompt
- Add `motor_plate` and `gearbox_plate` schemas
- Build deterministic geometry templates
- Wire validated order form to CAD generation pipeline
