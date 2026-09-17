# API Contracts

The finalized API contract reference, per
`01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md` "Documentation Requirements".
This document describes what the backend actually implements (verified against the real
schema files and a live running server during Phase 06), not an aspirational design — the
FastAPI-generated OpenAPI schema (`GET /openapi.json`, `GET /docs`) remains the
machine-readable source of truth; this is the human-readable companion, and the frontend's
`frontend/src/api-client/types.ts` mirrors it field-for-field.

All endpoints are versioned under `/api/v1` except `/health`, which is unversioned by
design (`ARCHITECTURE.md` "API Contract Philosophy").

---

## Conventions

- **Errors:** two shapes exist. Every application-level failure (unknown dataset, bad
  request shape the domain module itself rejects, provider misconfiguration, etc.) returns
  `{"error": {"code": string, "message": string}}` with a correctly-set status code.
  Request-shape validation failures caught by FastAPI/Pydantic before application code
  runs (missing required field, wrong type) return `{"detail": [...]}`, standard FastAPI
  422 shape. `frontend/src/api-client/http.ts` normalizes both into one `ApiError`.
- **IDs:** every `dataset_id` is a server-generated UUID (`app/ingestion/storage.py`) —
  never derived from the client's filename, which is the structural path-traversal
  defense (`ARCHITECTURE.md` "Data Storage").
- **Timestamps:** every datetime field is an ISO-8601 string in the JSON response.

---

## Health

### `GET /health`
No auth, no dataset scope. Returns `{status, service, environment, timestamp}`.

---

## Ingestion (`backend/app/api/datasets.py`)

### `POST /api/v1/datasets`
`multipart/form-data`, field `file` (CSV only, ≤50 MB per `APP_MAX_UPLOAD_SIZE_BYTES`).
Returns `201` + `DatasetMetadata` (`id, original_filename, uploaded_at, size_bytes,
row_count, column_count, columns: [{name, dtype}], missing_value_count,
duplicate_row_count`).

Errors: `missing_filename` (400), `unsupported_file_type` (400, only `.csv`), `empty_file`
(400), `file_too_large` (413).

### `GET /api/v1/datasets`
Returns `DatasetSummary[]` — the same core fields minus `columns`/`missing_value_count`/
`duplicate_row_count` (lighter shape for a list view).

### `GET /api/v1/datasets/{dataset_id}`
Returns the full `DatasetMetadata`. Errors: `dataset_not_found` (404).

There is no delete endpoint in this phase — datasets accumulate under
`backend/data/uploads/` until manually removed.

---

## Profiling (`backend/app/api/profile.py`)

All nested under `/api/v1/datasets/{dataset_id}/...`; every endpoint shares
`dataset_not_found` (404) / `dataset_unreadable` (500-class) as a possible error.

### `GET .../profile` → `DatasetProfile`
`row_count, column_count, memory_usage_bytes, duplicate_row_count,
duplicate_row_percentage, missing: {total_missing_cells, missing_percentage,
columns_with_missing}, columns: ColumnProfile[], generated_at`.

`ColumnProfile`: `name, pandas_dtype, semantic_type, null_count, null_percentage,
unique_count, unique_percentage, sample_values, numeric_stats | categorical_stats |
datetime_stats` (exactly one populated, matching `semantic_type`).

### `GET .../quality` → `QualitySummary`
`findings: QualityFinding[]` (`code, severity: info|warning|critical, column, message,
metric, details`), `finding_count, generated_at`.

### `GET .../columns/{column_name}` → `ColumnProfile`
Single-column detail. Errors: `column_not_found` (404).

### `GET .../correlation` → `CorrelationResult`
`method: "pearson", minimum_observations, eligible_columns, pairs: CorrelationPair[]
({column_a, column_b, coefficient, observations}), status: "computed"|"insufficient_data",
message, generated_at`. `status` is never silently empty — `insufficient_data` always
carries a human-readable `message`.

### `GET .../distribution` → `DistributionResult`
`columns: ColumnDistribution[] ({column, bin_count, bins: HistogramBin[]
({bin_start,bin_end,count}), min, max}), skipped_columns: string[], generated_at`.

---

## ML (`backend/app/api/ml.py`)

### `GET /api/v1/ml/task-types` (dataset-independent) → `TaskTypesResponse`
`task_types: [{task_type, label, description, supported_models}]` — the fixed set:
`binary_classification`, `multiclass_classification`, `regression`.

Nested under `/api/v1/datasets/{dataset_id}/ml/...` below:

### `POST .../ml/validate-target`
Body: `{target_column}`. Returns `ValidateTargetResponse`: `observed:
ObservedTargetFacts` (row/null/unique counts, dtype, semantic type — never opinion),
`suitable_tasks: [{task_type, suitable, reason}]`, `suggested_task | null`,
`is_suggestion: true` (always — this endpoint never commits to a task type). Errors:
`target_not_found` (404).

### `POST .../ml/train`
Body: `TrainRequest` (`target_column, task_type, model_name, test_size?, random_state?`).
Returns `ModelResult`: feature/exclusion facts, `preprocessing` summary,
`training_config`, `train_size, test_size_actual, metrics: Record<string, number>,
unavailable_metrics: Record<string, string>` (reason per metric that couldn't be
computed — never silently absent), `confusion_matrix | null`, `warnings, limitations,
generated_at`. "Train" and "evaluate" are one atomic operation (ADR-013) — there is no
separate persisted-model/evaluate-later flow.

Errors: `invalid_model_for_task` (400), and every `target_not_found`/insufficient-data
class of error `validate-target` would have also reported.

### `POST .../ml/compare`
Body: `CompareRequest` (`target_column, task_type, model_names[], test_size?,
random_state?`). Returns `ComparisonResult`: `results: ModelResult[]`, one per requested
model on the identical split — no aggregate score or declared winner.

---

## AI (`backend/app/api/ai.py`)

### `GET /api/v1/ai/status` (dataset-independent) → `AIStatusResponse`
`enabled, provider, model, available, reason`. Never includes a secret — no field could
hold one. `offline` (default) is always `available: true`.

Nested under `/api/v1/datasets/{dataset_id}/ai/...` below:

### `POST .../ai/analyze`
Body: `AIAnalyzeRequest` (`capability, column_name?, ml_result?`). `capability` is one of
`dataset_summary | quality_explanation | column_insight | correlation_explanation |
ml_explanation`. `column_name` required for `column_insight`; `ml_result` (a full
`ModelResult`, verbatim from `.../ml/train`) required for `ml_explanation` — there is no
model-persistence layer, so the caller supplies it directly (ADR-013).

Returns `AIAnalyzeResponse`: `computed` (the exact deterministic evidence, capability-shaped
— see `frontend/src/api-client/types.ts`'s `*Evidence` interfaces), `evidence_sources:
string[]`, `ai_explanation: {source: "ai_generated", provider, model, text, generated_at} |
null`, `grounded: true`, `limitations: string[]`, `available, reason`. **`computed` is
always present and correct regardless of `available`** — an unconfigured/failed AI
provider never blocks deterministic data (Phase 05's grounding guarantee).

Errors: `column_name_required` (400), `column_not_found` (404), `ml_result_required` (400),
`ml_result_malformed` (400), `dataset_not_found` (404).

### `POST .../ai/query`
Body: `AIQueryRequest` (`question, ml_result?`). Returns `AIQueryResponse`: same envelope
shape as `analyze`, plus `question, question_category:
deterministic_lookup|explanation|analytical_interpretation|unsupported`. `computed`
always includes `resolved_answer` (`string | null`) and, for `explanation`/
`analytical_interpretation` categories, a `context` field (the same shape as
`dataset_summary`'s evidence).

---

## Contract Verification

Verified during Phase 06 by starting the real backend and frontend together and exercising
every endpoint above through the actual UI (not mocked) — see
`01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_REPORT.md` "Tests/checks" for the exact
run. The frontend's `frontend/src/api-client/*.test.ts` files additionally pin each
function's request/response shape against a mocked `fetch`, so a future backend contract
change that isn't reflected in `types.ts` fails a frontend test, not just a silent runtime
mismatch.

---
*Related: [ARCHITECTURE.md](ARCHITECTURE.md) "API Contract Philosophy",
"AI Analytics Architecture (Phase 05)", "Frontend Integration Architecture (Phase 06)" ·
[decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md)*
