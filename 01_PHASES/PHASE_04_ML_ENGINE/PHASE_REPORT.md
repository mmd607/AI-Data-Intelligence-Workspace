# Phase Report

## Phase
PHASE 04 — ML Engine

## Date
2026-09-17

## Branch
`phase/04-ml-engine` (branched from `origin/main` at `b7c4d86`, the human-merged,
Phase-03-included baseline)

## What was built

- **`backend/app/ml/`** — a 12-file module, isolated from `ingestion/`/`profiling/`/`api/`
  per `02_DOCS/ARCHITECTURE.md` "Module Boundaries":
  - `errors.py` — `MLError` (independent of `IngestionError`/`ProfilingError`, identical
    envelope).
  - `schemas.py` — every Pydantic model, explicitly separating observed facts, task type,
    features, preprocessing, model, metrics, warnings, and limitations (this phase's Core
    Principle).
  - `task_detection.py` / `task_info.py` — deterministic task-type suitability evaluation
    (reusing Phase 03's `detect_semantic_type`) and static task-type/model metadata.
  - `target_validation.py` — target existence, all-missing, insufficient-rows,
    single-class, cardinality-mismatch, class-imbalance-warning, and type-incompatibility
    checks, each with a specific error code.
  - `preprocessing.py` — feature selection (excludes target-duplicates, constant columns,
    free-text/datetime/unknown-typed columns) and `ColumnTransformer` construction
    (median-impute + scale for numeric; most-frequent-impute + one-hot for categorical;
    infinite values cleaned to `NaN` before imputation).
  - `splitting.py` — deterministic, stratified-where-appropriate train/test split with
    explicit `invalid_split_configuration` guards.
  - `models.py` — the fixed baseline registry (`LogisticRegression`/
    `RandomForestClassifier`; `LinearRegression`/`Ridge`/`RandomForestRegressor`).
  - `evaluation.py` — classification (accuracy/precision/recall/F1/confusion
    matrix/ROC-AUC where valid) and regression (MAE/MSE/RMSE/R² where valid) metrics, with
    an explicit `unavailable_metrics` map for anything mathematically invalid.
  - `training.py` — orchestration: validate → drop null-target rows → select features →
    split once → fit+evaluate one model's `Pipeline`.
  - `comparison.py` — multiple models over the identical prepared split, no aggregate
    score, no declared winner.
- **`backend/app/api/ml.py`** — 4 endpoints: `GET /api/v1/ml/task-types` (dataset-
  independent), `POST /api/v1/datasets/{id}/ml/validate-target`, `.../ml/train`,
  `.../ml/compare`. Thin router only.
- **`backend/app/main.py`** — mounted both ML routers; registered an `MLError` exception
  handler (same structured envelope, independent class).
- **Dependencies added**: `scikit-learn==1.5.2`, `scipy==1.14.1` (pinned explicitly after
  discovering a real version-skew warning between `scikit-learn` and the newest available
  `scipy` — see "Known limitations" and ADR-013).
- **3 new fixture datasets** (`ml_classification.csv`, `ml_multiclass.csv`,
  `ml_regression.csv`, 40-80 rows each, reproducibly generated with a fixed seed, real
  signal between features and target so training produces meaningful, non-random metrics).
- **233 backend tests total (92 new)** across 9 new test files: golden-value unit tests
  for every ML submodule (constructed DataFrames, no file I/O, matching Phase 03's
  established pattern), a dedicated leakage-prevention test class, a determinism test
  class (repeated training with the same seed produces byte-identical metrics), and a full
  API integration suite covering all 4 endpoints and their structured error paths.

## Architecture decisions

- **ADR-004 finalized**: XGBoost was concretely benchmarked (temporarily installed, run
  against equivalent scikit-learn baselines on synthetic classification/regression data,
  then uninstalled) — real numbers recorded, **not adopted**. See the ADR for the full
  benchmark table and reasoning (real but marginal classification gain, more notable
  regression gain on synthetic data that likely doesn't transfer to this project's much
  smaller real fixture datasets; not worth the dependency cost against the phase's
  explicit "no model zoo" instruction).
- **ADR-013 (new)**: records the model set, preprocessing strategy, the deliberate
  train+evaluate merge (no model-persistence layer exists, so there's nothing to
  "evaluate" later that training doesn't already produce), the non-null-target-row
  feasibility semantics, the `average="weighted"` metric choice, and the `scipy` pin.
- `02_DOCS/ARCHITECTURE.md` gained a "Machine Learning Architecture (Phase 04)" section.

## Files/components added or changed

New: 12 files under `backend/app/ml/`, `backend/app/api/ml.py`, 3 fixture CSVs, 9 new test
files, `01_PHASES/PHASE_04_ML_ENGINE/PHASE_REPORT.md`.
Changed: `backend/app/main.py` (router mounts + exception handler),
`backend/requirements.txt` (+scikit-learn, +scipy), `02_DOCS/ARCHITECTURE.md`,
`02_DOCS/TESTING_STRATEGY.md`, `02_DOCS/decisions/DECISIONS_LOG.md` (ADR-004 finalized,
ADR-013 added), `00_AGENT_CONTROL/PROJECT_STATE.md`.
Verified unchanged: `backend/app/ingestion/`, `backend/app/profiling/`,
`backend/app/api/datasets.py`, `backend/app/api/profile.py` — no Phase 02/03 regression
(confirmed via `git status` showing no diffs to those paths, and the full 233-test suite,
including every pre-existing Phase 02/03 test, still passing).

## Tests/checks

- Command: `ruff check .` → Result: **All checks passed.**
- Command: `pytest -q` → Result: **233 passed**, 0 failed, 0 skipped (92 new; all 141
  pre-existing Phase 01-03 tests still green — no regression).
- Command: `pytest --cov=app.ml --cov-report=term-missing` → Result: **100% line
  coverage** on `app/ml/` — every branch, including a NaN-poisoned ROC-AUC input and a
  high-cardinality categorical-feature warning, is exercised by a genuine test.
- Real server verification (not just automated tests): started `uvicorn` for real,
  uploaded all three ML fixtures via `curl -F`, then called every endpoint against the
  real running server:
  - `GET /ml/task-types` → real `200` with all 3 task types and their supported models.
  - `POST .../validate-target` → real, correct suitability facts and a labeled suggestion.
  - `POST .../train` → real binary, multiclass, and regression training runs, each with
    genuine computed metrics (e.g. binary classification: accuracy 0.875, ROC-AUC 0.875,
    real confusion matrix).
  - `POST .../compare` → 2 real model results under the identical split, no `winner` field.
  - Error paths verified live: `invalid_model_for_task` (400), `dataset_not_found` (404),
    `target_type_incompatible` (400).
  - **Determinism verified over real HTTP**, not just in-process: two separate `curl`
    calls with the same `random_state` produced byte-identical `metrics`.
  - `/docs` returned `200`; `/openapi.json` parsed as valid JSON and listed all 4 new
    paths.
  - Verification data directory removed afterward.
- Confirmed no out-of-scope functionality introduced: `grep -rniE
  "anthropic|openai|claude|three\.js|react-three" app/` returned no matches (no Phase 05
  AI or 3D UI code).

## Known limitations

- `scipy` had to be explicitly pinned to `1.14.1` (alongside `scikit-learn==1.5.2`) after
  discovering that the newest available `scipy` (1.18.1) triggers a real
  `OptimizeWarning` from `LogisticRegression`'s lbfgs solver passing a now-unrecognized
  solver option — a genuine upstream version-skew issue, verified and resolved, not
  silently ignored (see ADR-013).
- No model-persistence/serving layer exists (explicitly out of scope per the phase
  prompt) — "train" and "evaluate" are therefore one atomic operation, not two separate
  stateful steps. Documented as a deliberate architectural choice in ADR-013, not an
  oversight.
- `test_size`/`random_state` overrides for distribution binning and correlation's
  `minimum_observations` (Phase 03) remain function parameters without a corresponding
  API query parameter — consistent with the equivalent Phase 03 limitation, still not
  needed until a frontend phase requires tuning them.
- The `unexpected_negative_values`-style domain heuristics from Phase 03's quality engine
  were deliberately **not** duplicated into the ML layer's target/feature validation —
  target validation focuses on structural training-feasibility, not data-quality opinions,
  which remain Phase 03's responsibility; a caller wanting quality context can call the
  Phase 03 endpoints first.
- High-cardinality categorical features (>50 distinct values) produce a warning but are
  still one-hot encoded as-is in v1 — no automatic frequency-capping or target-encoding
  fallback; noted as a real limitation for a future phase, not silently absent.

## Git

Commits (on `phase/04-ml-engine`): recorded in the completion message — hash cannot be
self-referenced in this file within the same commit that includes it.

Remote branch: `origin/phase/04-ml-engine` — pushed and existence verified (see completion
message).

## Next phase

**PHASE 05 — AI Analytics**
(`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`). Not started. Requires explicit human
approval before beginning.
