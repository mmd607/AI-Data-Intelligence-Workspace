# PHASE 03 — DATA PROFILING & VISUALIZATION

## Objective
Turn ingested data into trustworthy analytical information and visualization-ready data.

## Analytics
Implement structured calculations for:
- descriptive statistics;
- numeric distributions;
- categorical frequencies;
- missingness;
- duplicates;
- correlations where mathematically appropriate;
- outlier indicators where appropriate.

## Visualization
Prepare frontend-ready data for:
- histograms;
- bar charts;
- scatter plots;
- correlation views;
- missingness views;
- summary cards.

The frontend can remain 2D here. The 3D universe belongs to Phase 07.

## Trust
Every value shown must be traceable to a backend calculation.

## Output
Document analytical decisions, edge cases, and API contracts.
Run tests, update state, commit, push. Do not merge.

---

## Scope

This phase covers two closely related concerns: (1) a deterministic, rule-based **data
quality profile** (nulls, dtypes, duplicate rows, basic distribution shape, outlier flags,
a transparent and versioned quality score), and (2) **descriptive statistics and
visualization-ready data** (the Analytics/Visualization lists above) plus the first real
(non-3D) chart components in the frontend, and finalizing the chart-library choice
(`../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-002 — visx, pending confirmation here).

## Non-Goals

ML modeling (Phase 04), AI explanations of the profile/statistics (Phase 05 wires the
*explanation*; this phase only builds the *data* it will explain), the 3D Universe
(Phase 07 — frontend stays 2D here).

## Inputs

Phase 02 ingestion output.

## Outputs

`/api/v1/datasets/{id}/profile` and `/api/v1/datasets/{id}/statistics`, returning
structured, deterministic results; frontend 2D chart components (`frontend/src/viz/`)
consuming them.

## Files/Components Expected

`backend/app/profiling/` (profiler, scoring, statistics), `backend/app/api/profile.py`,
`backend/app/api/statistics.py`, `frontend/src/viz/`.

## Testing Requirements

Backend: unit tests against fixture datasets with known, engineered characteristics (known
null counts, known duplicate rows, known mixed types) asserting exact expected output
("golden value" tests); a determinism test (same input → identical output across runs);
statistic calculations cross-checked against direct `pandas`/`numpy` reference
calculations. Frontend: component render/unit tests for chart components (data-in,
correct-output-out, not pixel-perfect visual tests). See
`../../02_DOCS/TESTING_STRATEGY.md` §5.

## Acceptance Criteria

Profiling results are reproducible; the quality-score formula is documented and versioned
(a `score_version` field in the response); missing/uncomputable values are surfaced as
`null`/`"N/A"`, never fabricated as `0` (product principle 1 — hard rule, matches this
phase's own "Trust" section above); computed statistics match reference calculations
exactly (within floating-point tolerance); charts render real computed data end-to-end from
a real uploaded dataset through to the browser.

## Documentation Requirements

Create `../../02_DOCS/DATA_AND_SCORING.md` documenting the exact quality-scoring
methodology and its version; confirm or revise `../../02_DOCS/decisions/DECISIONS_LOG.md`
ADR-002 (chart library) with real evidence from this phase; update
`../../02_DOCS/UI_UX_SPEC.md` §7 if 2D chart component states diverge from the general
component inventory.

## Branch

`phase/03-profiling-visualization`. Child branches as needed:
`backend/03-profiling-visualization-*`, `frontend/03-profiling-visualization-*`.

## Rollback Considerations

The profiling/statistics/viz modules are additive and isolated from ingestion; safe to
revert independently, no dependents yet.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
