# Phase Report

## Phase
PHASE 03 — Data Profiling & Visualization

## Date
2026-09-17

## Branch
`phase/03-data-profiling-visualization` (branched from `origin/main` at `cdd25f0`, the
Phase-02-merged, post-attribution-cleanup baseline)

## What was built

- **`backend/app/profiling/`** — a 13-file module, isolated from `ingestion/`/`api/` per
  `02_DOCS/ARCHITECTURE.md` "Module Boundaries":
  - `errors.py` — `ProfilingError` (independent of `IngestionError`, identical envelope).
  - `schemas.py` — every Pydantic response model: `DatasetProfile`, `ColumnProfile` (+
    `NumericColumnStats`/`CategoricalColumnStats`/`DatetimeColumnStats`), `QualitySummary`/
    `QualityFinding`, `CorrelationResult`/`CorrelationPair`, `DistributionResult`/
    `ColumnDistribution`/`HistogramBin`.
  - `loader.py` — loads a dataset's DataFrame via `ingestion.StorageService` (extended
    with one new public method, `get_raw_file_path` — no second storage system built).
  - `column_types.py` — conservative semantic-type classification (numeric/boolean/
    datetime/categorical/text/unknown), never overriding the raw pandas dtype, only
    interpreting it.
  - `numeric_stats.py`, `categorical_stats.py`, `datetime_stats.py` — per-type
    descriptive statistics.
  - `column_profile.py`, `dataset_profile.py` — per-column and whole-dataset
    orchestration.
  - `quality.py` — deterministic quality findings (missing values, duplicates,
    constant/near-constant columns, high-cardinality categoricals, mixed-type columns,
    infinite values, unexpected negatives in presumed-non-negative columns, invalid
    datetime values, empty dataset, zero columns).
  - `correlation.py` — pairwise Pearson correlation with an explicit
    `"insufficient_data"` status.
  - `distribution.py` — `numpy.histogram`-based binning for numeric columns.
- **`backend/app/api/profile.py`** — 5 endpoints, mounted under `/api/v1/datasets/
  {dataset_id}/`: `GET /profile`, `GET /quality`, `GET /columns/{column_name}`,
  `GET /correlation`, `GET /distribution`. Thin router only.
- **`backend/app/main.py`** — mounted the profiling router; registered a `ProfilingError`
  exception handler (same structured envelope as `IngestionError`, independent class).
- **`backend/app/ingestion/storage.py`** — added `get_raw_file_path(dataset_id)`, the one
  deliberate extension of Phase 02's storage interface this phase needed.
- **7 new test fixtures**: `profiling_dataset.csv` (mixed numeric/categorical/datetime
  with a known duplicate row and one known missing value), `profiling_constant.csv`
  (constant + exactly-95%-near-constant columns), `profiling_quality_edge.csv`
  (infinite values + a negative "age"). Phase 02's `header_only.csv` reused for the
  0-row edge case.
- **138 backend tests total (96 new)**: golden-value unit tests for every statistics
  module (constructed `pandas.Series`/`DataFrame`, no file I/O — see
  `02_DOCS/TESTING_STRATEGY.md` §5's newly-documented pattern), a dedicated loader test
  file covering out-of-band file corruption/removal, and a full API integration suite
  covering all 5 endpoints, their error paths, and determinism.

## Architecture decisions

- **ADR-011** (new): the fixed, documented thresholds behind every quality check, the
  Pearson/pairwise correlation strategy, the histogram binning strategy, and the
  infinite-value handling policy (excluded from descriptive stats, counted separately,
  flagged as a critical quality finding — `inf`/`NaN` are not valid JSON number tokens).
- `02_DOCS/ARCHITECTURE.md` gained a full "Profiling Architecture (Phase 03)" section
  documenting the module breakdown, edge-case policy, and the three strategies above.
- `02_DOCS/TESTING_STRATEGY.md` §5 records the unit-vs-integration test pattern this
  phase established (direct pandas construction for pure-function unit tests; fixture
  CSVs only for API-level round-trip tests) as a recommendation for Phase 04+.

## Files/components added or changed

New: 13 files under `backend/app/profiling/`, `backend/app/api/profile.py`, 3 new fixture
CSVs, and 11 new test files: `test_profile_api.py` plus
`test_profiling_{column_types,numeric_stats,categorical_stats,datetime_stats,
column_profile,dataset_profile,quality,correlation,distribution,loader}.py` (10 files),
`01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_REPORT.md`.
Changed: `backend/app/main.py` (router mount + exception handler),
`backend/app/ingestion/storage.py` (`get_raw_file_path`), `02_DOCS/ARCHITECTURE.md`,
`02_DOCS/TESTING_STRATEGY.md`, `02_DOCS/decisions/DECISIONS_LOG.md`,
`00_AGENT_CONTROL/PROJECT_STATE.md`.

## Tests/checks

- Command: `ruff check .` → Result: **All checks passed** (one project-standard
  isinstance-union style fix applied via `--fix --unsafe-fixes`, rest fixed by hand for
  line length).
- Command: `pytest -q` → Result: **138 passed**, 0 failed, 0 skipped (96 new).
- Command: `pytest --cov=app.profiling --cov-report=term-missing` → Result: **99% line
  coverage** on `app/profiling/`. The single uncovered line is a provably-unreachable
  defensive guard inside a private helper (`_looks_like_plain_integers`'s empty-input
  check — its only caller already checks the same condition first) — left uncovered
  deliberately per the "not meaningless coverage inflation" standard, rather than adding a
  contrived direct test of a private function or stripping a harmless safety check.
- Real server verification (not just automated tests): started `uvicorn` for real,
  uploaded `profiling_dataset.csv` via `curl -F`, then called all 5 new endpoints against
  the real running server and confirmed real, correct computed values (duplicate row
  count, missing-cell count, per-column stats, quality findings, correlation
  insufficient-data status, histogram bins). `/docs` returned `200`; `/openapi.json`
  parsed as valid JSON and listed all 5 new paths. Verification data directory removed
  afterward.
- Confirmed no Phase 04 functionality was introduced: `grep -rniE
  "sklearn|scikit|xgboost|\.fit\(|\.predict\(|train_test_split|RandomForest|
  LinearRegression" app/` returned no matches.

## Known limitations

- No caching layer for loaded DataFrames — every profiling endpoint re-reads the CSV from
  disk. Acceptable for a local-first v1 (documented in `loader.py` and
  `02_DOCS/ARCHITECTURE.md`); revisit if profiling becomes a measured hot path.
- Semantic-type detection is heuristic (fixed thresholds, not learned) and conservative by
  design — a column that's borderline between two types (e.g. 85% date-parseable) falls
  back to the safer classification (categorical) rather than guessing. This is intentional
  per the phase's own "do not make aggressive semantic assumptions" instruction, not a gap.
- The `unexpected_negative_values` quality check uses a small, fixed keyword list on the
  column name (`age`, `price`, `amount`, `quantity`, `qty`, `count`, `total`) to decide
  whether negative values are "unexpected" — a deliberately narrow, documented heuristic,
  not general domain knowledge; a column named something else with genuinely unexpected
  negatives won't be flagged by this specific check (though `infinite_values` and other
  checks are name-independent).
- Distribution bin count (10) and correlation `minimum_observations` (3) are fixed
  defaults; both functions accept an override parameter, but no API query parameter
  exposes that override yet — deferred as unnecessary for this phase's contract, not
  forgotten (would be a small addition to `api/profile.py` if Phase 06/07's frontend needs
  it).

## Git

Commits (on `phase/03-data-profiling-visualization`): recorded in the completion message
— hash cannot be self-referenced in this file within the same commit that includes it.

Remote branch: `origin/phase/03-data-profiling-visualization` — pushed and existence
verified (see completion message).

## Next phase

**PHASE 04 — ML Engine**
(`01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md`). Not started. Requires explicit human
approval before beginning.
