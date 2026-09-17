"""Dataset ingestion — upload, validation, parsing, and storage.

Scope is deliberately narrow, per `01_PHASES/PHASE_02_DATA_INGESTION/PHASE_PROMPT.md`:
structural facts extracted during parsing (row/column counts, dtypes, a raw missing-value
count, a raw duplicate-row count) — never a quality score, distribution shape, outlier
flag, or correlation. Those belong to Phase 03's profiling/analytics engine, which is a
separate module that will consume this one's stored output, not extend it.
"""
