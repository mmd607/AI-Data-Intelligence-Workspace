# PHASE 02 — DATA INGESTION

## Objective
Build a reliable dataset ingestion layer, starting with CSV.

## Tasks
- CSV upload/input pipeline;
- file validation;
- encoding handling;
- delimiter detection where practical;
- schema extraction;
- row/column counts;
- data type inference;
- missing-value detection;
- duplicate-row detection;
- safe temporary storage;
- structured ingestion result;
- clear errors for invalid files.

## API
Create clean FastAPI endpoints for ingestion and dataset metadata.

## Tests
Include valid CSV, empty CSV, malformed CSV, missing values, duplicate rows,
mixed types, and large-ish local test fixtures.

## Constraint
Do not build ML or AI explanations yet.

## Output
Phase report + PROJECT_STATE update + committed and pushed non-main branch.

---

## Scope

Dataset upload, validation, storage, and metadata retrieval — the first real feature.
Upload endpoint(s), file-type/size validation, a storage layer (resolving the storage
decision left open in `../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-005 — filesystem +
JSON sidecars by default, SQLite if this phase finds that insufficient), dataset
list/get endpoints, Pydantic schemas for dataset metadata.

## Non-Goals

No profiling/quality scoring, no statistics, no ML, no AI layer, no 3D UI wiring (API only
— this phase's output is consumed by later phases, not rendered yet).

## Inputs

Phase 01 scaffold; `../../02_DOCS/ARCHITECTURE.md` "Data Storage", "API Contract
Philosophy", and "Security & Privacy" sections.

## Outputs

Working `/api/v1/datasets` endpoints (create/list/get, at minimum).

## Files/Components Expected

`backend/app/ingestion/` (validation, storage service), `backend/app/api/datasets.py`,
Pydantic schemas.

## Testing Requirements

Unit tests for validation logic (accepted/rejected file types, size-limit enforcement,
path-traversal/malicious-filename handling); integration tests for the
upload→list→get flow using FastAPI's `TestClient`; the fixture set named in "Tests" above
(valid/empty/malformed CSV, missing values, duplicate rows, mixed types, a large-ish
fixture) lives under `backend/tests/fixtures/` per `../../02_DOCS/TESTING_STRATEGY.md`.

## Acceptance Criteria

All of the ZIP's original "Acceptance"-equivalent bar above, plus: a dataset can be
uploaded via the API and its metadata retrieved; invalid files are rejected with clear,
structured error responses (never a bare 500); all required tests pass.

## Documentation Requirements

`../../02_DOCS/ARCHITECTURE.md` "Data Storage" decision finalized (❓→✅, or a new choice,
with `../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-005 updated accordingly); dataset
size/type limits (❓ in `../../02_DOCS/PRODUCT_SPEC.md` "Open Questions") resolved and
documented; OpenAPI docs verified to render correctly.

## Branch

`phase/02-data-ingestion`. Child branches as needed: `backend/02-data-ingestion-*`.

## Rollback Considerations

The ingestion module is self-contained; reverting removes upload capability without
affecting the Phase 01 scaffold.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
