# FRC Text-to-CAD Tool

## Project Overview
A tool that converts plain English part descriptions into parametric CAD geometry for FRC robotics.

## Architecture
1. **Frontend**: Student enters plain English part description
2. **Backend**: Python processes description via Claude API, outputs JSON order form
3. **Validator**: Checks JSON structure and constraints
4. **Template Engine**: Generates parametric CAD geometry from validated order

## Current Phase
Building frontend skeleton - a static HTML/CSS/JS page with text input and result display.

## Tech Stack
- Frontend: Plain HTML/CSS/JavaScript (no frameworks)
- Backend: Python with Claude API
- Data: JSON order forms

## Next Steps
- Implement backend parser
- Build validator
- Create parametric geometry templates
