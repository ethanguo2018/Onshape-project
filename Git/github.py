# FRC Text-to-CAD Tool

Turns a plain English sentence into a manufacturable, parametric CAD part for FIRST Robotics teams.

Example: "gusset joining two 2x1 MAXTubes at 60 degrees, four #10 holes per side" becomes router-ready geometry in under a minute.

## How it works
1. Student types a part description
2. One Claude API call parses it into a JSON order form
3. A validator checks the order form against real COTS dimensions
4. Deterministic parametric templates generate the geometry

## Status
Early development, June 2026. Building the front end skeleton and vertical slice.

## Team
Peter Shen and Ethan Guo