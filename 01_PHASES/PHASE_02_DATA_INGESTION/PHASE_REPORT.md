# Phase Report

## Phase
PHASE 02 — Data Ingestion

## Date
2026-09-17

## Branch
`phase/02-data-ingestion` (branched from `origin/main` at `56ffd8d`, the human-approved
Phase 01 baseline, since local `main` was behind — see Git identity/workflow discussion
preceding this phase)

## What was built

- **`backend/app/ingestion/`** — the ingestion module, isolated from `api/` per
  `02_DOCS/ARCHITECTURE.md` "Module Boundaries":
  - `errors.py` — `IngestionError` (a stable machine-readable `code` + HTTP status).
  - `schemas.py` — `ColumnInfo`, `DatasetMetadata`, `DatasetSummary`, `ErrorResponse`.
    Deliberately contains only structural facts (row/column counts, dtypes, a raw
    missing-value count, a raw duplicate-row count) — no quality score, distribution, or
    outlier field; that is Phase 03's module to build, not this one's to anticipate.
  - `validation.py` — `sanitize_filename` (strips POSIX/Windows path components for
    *display* only), `validate_extension` (`.csv` only), `validate_size` (rejects 0 bytes
    and anything over the configured limit).
  - `parsing.py` — `parse_csv`: decodes text (UTF-8/UTF-8-BOM/Latin-1 fallback), rejects
    binary content disguised as `.csv` via a printable-character heuristic, then parses
    with `pandas` and extracts row/column counts, per-column dtypes, total missing-cell
    count, and duplicate-row count. Pure function of the input bytes — deterministic,
    tested for it directly.
  - `storage.py` — `StorageService`: writes `original.csv` + `metadata.json` under
    `<base_dir>/<dataset_id>/`, where `dataset_id` is always server-generated (`uuid4`),
    never derived from client input — the structural path-traversal defense.
- **`backend/app/api/datasets.py`** — `POST /api/v1/datasets` (upload, 201), `GET
  /api/v1/datasets` (list), `GET /api/v1/datasets/{id}` (get, 404 if unknown). Thin router
  only — validates via the ingestion module, shapes the response, no business logic.
- **`backend/app/main.py`** — mounted the datasets router under `/api/v1`; registered an
  `IngestionError` exception handler returning the project's structured error envelope
  (`{"error": {"code", "message"}}`) with the correct status code (400/404/413), distinct
  from the catch-all 500 handler from Phase 01.
- **`backend/app/config.py`** — added `data_dir` and `max_upload_size_bytes` settings,
  resolving the two open questions this phase was scoped to close.
- **Test fixtures** (`backend/tests/fixtures/`): `valid.csv`, `header_only.csv`,
  `empty.csv` (genuinely 0 bytes), `malformed.csv` (ragged row triggers a real
  `pandas.errors.ParserError`), `missing_values.csv` (4 known blank cells),
  `duplicate_rows.csv` (3 known duplicate rows), `mixed_types.csv` (forces an `object`
  dtype column). The "large-ish" case (5,000 rows) is generated in memory by a test
  helper rather than committed, per `02_DOCS/TESTING_STRATEGY.md` §7.
- **42 backend tests total** (34 new): `test_ingestion_validation.py` (filename
  sanitization/path-traversal stripping, extension rules, size rules),
  `test_ingestion_parsing.py` (golden-value tests against every fixture, determinism,
  error cases, the large-ish case), `test_datasets_api.py` (the full upload→list→get flow,
  a same-file-twice determinism check, 404 on unknown id, structured 400/413 error
  responses, a dedicated path-traversal-filename API test asserting the file never
  escapes the isolated storage directory, and an oversized-file 413 test using a
  dependency-overridden tiny size limit).

## Architecture decisions

- **ADR-005** (Dataset & Metadata Storage) resolved from ❓ to ✅: filesystem +
  JSON-sidecar confirmed sufficient for v1, no database.
- **ADR-010** (new): Upload size limit (50 MB) and supported file type (`.csv` only, with
  a binary-content sniff against MIME spoofing) — both `02_DOCS/PRODUCT_SPEC.md` open
  questions resolved. Streaming-based early rejection of oversized uploads (vs. the
  current buffer-then-check approach) is explicitly deferred to Phase 08, not silently
  skipped.
- Added a small Ruff config exception (`extend-immutable-calls` for
  `fastapi.Depends`/`File`/`Query`/`Body`) — FastAPI's own documented dependency-injection
  pattern otherwise trips Ruff's generic mutable-default-argument rule (B008); this is a
  standard, widely-used configuration for FastAPI codebases, not a suppression of a real
  bug.

## Files/components added or changed

New: `backend/app/ingestion/{__init__,errors,schemas,validation,parsing,storage}.py`,
`backend/app/api/datasets.py`, 7 fixture files under `backend/tests/fixtures/`,
`backend/tests/conftest.py`, `backend/tests/test_ingestion_validation.py`,
`backend/tests/test_ingestion_parsing.py`, `backend/tests/test_datasets_api.py`,
`01_PHASES/PHASE_02_DATA_INGESTION/PHASE_REPORT.md`.
Changed: `backend/app/main.py` (router mount + exception handler), `backend/app/config.py`
(new settings), `backend/requirements.txt` (+pandas, +numpy, +python-multipart),
`backend/pyproject.toml` (Ruff config), `backend/.env.example`, `.gitignore`
(`backend/data/` — the actual on-disk location the new `data_dir` default resolves to),
`02_DOCS/ARCHITECTURE.md` (Data Storage section finalized), `02_DOCS/PRODUCT_SPEC.md`
(Open Questions resolved), `02_DOCS/decisions/DECISIONS_LOG.md` (ADR-005 updated, ADR-010
added), `00_AGENT_CONTROL/PROJECT_STATE.md`.

## Tests/checks

- Command: `ruff check .` → Result: **All checks passed.**
- Command: `pytest -q` → Result: **42 passed**, 0 failed, 0 skipped (34 new + the 8 from
  Phase 01, all still green).
- Real server verification (not just automated tests): started `uvicorn` for real,
  uploaded `valid.csv` via `curl -F` → got a real `201` with correct computed fields;
  listed datasets → the upload appeared; uploaded `malformed.csv` → real `400`
  `malformed_csv`; uploaded a `.json`-named file → real `400` `unsupported_file_type`;
  `/docs` returned `200`; `/openapi.json` includes both `/api/v1/datasets` and
  `/api/v1/datasets/{dataset_id}`. Verification data directory removed afterward.
- **Re-verified on request** after the human merged this branch into `main` (PR #2,
  `370cf4e`): fresh `pytest -q` → still **42 passed**; fresh `ruff check .` → still all
  checks passed; `git diff` against both the last local commit and
  `origin/phase/02-data-ingestion` confirmed empty (nothing outstanding). No code changes
  were needed — see `00_AGENT_CONTROL/PROJECT_STATE.md` agent log for the full note.

## Known limitations

- Oversized uploads are rejected **after** the file is fully read into memory, not via an
  early `Content-Length`-based streaming rejection — documented as an accepted, deferred
  risk in ADR-010, to be hardened in Phase 08 ("Testing, Security & Reliability"), not
  silently ignored.
- No row/column count ceiling beyond the 50 MB byte cap — consistent with the
  already-documented "fits in memory" assumption; revisit if a real dataset needs it.
- File-type validation is extension + content-heuristic based, not a full MIME-sniffing
  library (`python-magic` was considered and explicitly deferred in ADR-010 to avoid an
  unjustified new dependency at this phase).
- Concurrent writes to the same `dataset_id` are not specifically guarded against (not a
  realistic concern in v1 — ids are server-generated per request), but this isn't a
  general-purpose concurrent-write-safe store; noted for Phase 08 awareness, not a defect
  found in this phase's own scope.

## Git

Commits (on `phase/02-data-ingestion`): `33f1981` — `feat: Phase 02 dataset ingestion
(backend)`, followed by a small commit recording this hash back into this report and
`PROJECT_STATE.md` (unavoidable, same reason as Phase 01).

Remote branch: `origin/phase/02-data-ingestion` — pushed and existence verified (see
completion message).

## Next phase

**PHASE 03 — Data Profiling & Visualization**
(`01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`). Not started. Requires
explicit human approval before beginning.
