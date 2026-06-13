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

**Frontend Skeleton** — Building the UI for students to submit part descriptions.

- Single static HTML page with text input, submit button, and result display
- Future: Will POST to `/parse` backend endpoint and display JSON response

**Next Phase**: Backend implementation with Claude API integration and geometry template engine.

## Example Flow

1. Student types: "gusset joining two 2x1 MAXTubes at 60 degrees"
2. Frontend submits to backend `/parse`
3. Claude API parses → `{ "type": "gusset", "tube_size": "2x1", "angle": 60 }`
4. Backend validates
5. Deterministic template generates CAD geometry
6. Result returned to frontend and displayed

## Order Form Schemas

JSON Schemas live in `schemas/`. Each file defines the contract the Claude parser must fill and the validator must check before geometry generation.

- `schemas/gusset.schema.json` — JSON Schema draft 2020-12 for gusset order forms
- `schemas/gusset.example.json` — one valid filled-in example

**Note:** enum values and numeric bounds are placeholders pending Peter's review.

## Next Steps
- Implement backend parser
- Build validator
- Create parametric geometry templates
