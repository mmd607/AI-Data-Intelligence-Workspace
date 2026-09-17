"""Data profiling, quality analysis, correlation, and distribution computation.

Scope, per `01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`: every value
this module returns is computed deterministically from the actual dataset via
pandas/NumPy — never fabricated, estimated, or hard-coded. No ML (Phase 04) and no AI
explanation (Phase 05) logic lives here; this module only produces the structured,
computed facts those later phases (and the frontend) will consume or explain.
"""
