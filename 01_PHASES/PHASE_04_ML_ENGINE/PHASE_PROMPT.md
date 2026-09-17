# PHASE 04 — ML ENGINE

## Objective
Add a controlled baseline machine-learning layer.

## Tasks
- dataset suitability checks;
- feature/target selection workflow;
- preprocessing pipeline;
- train/test split;
- baseline classification and/or regression depending on data;
- metrics;
- feature importance/explainability where valid;
- model metadata;
- reproducible random seeds.

Prefer scikit-learn. Use XGBoost only when it materially adds value and is justified.

## Safety
Do not claim predictive quality beyond measured metrics.
Do not automatically choose a target if doing so would be misleading.
Expose assumptions.

## API
Return structured model results suitable for UI and later AI explanation.

## Output
Tests + documentation + phase report + state update + non-main branch push.

---

## Scope

Feature preparation, train/test split, baseline model(s) (e.g. a linear/logistic model and
a tree-ensemble model), metrics computation (accuracy/F1/RMSE/R² as appropriate to task
type), result storage, and a concrete, evidence-based XGBoost evaluation (accuracy delta
vs. dependency cost on fixture datasets) closing out
`../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-004.

## Non-Goals

Hyperparameter tuning UI, AutoML, deep learning, AI-generated commentary on results
(Phase 05 — and even then, AI may only narrate these metrics, never alter or invent them,
per product principle 3).

## Inputs

Phase 02/03 outputs (a validated, profiled dataset).

## Outputs

`/api/v1/datasets/{id}/ml/*` endpoints for triggering a run and fetching results.

## Files/Components Expected

`backend/app/ml/` (feature prep, training, evaluation), `backend/app/api/ml.py`.

## Testing Requirements

Unit tests per pipeline stage; a reproducibility test (fixed random seed → metrics stable
within a defined tolerance across runs, matching this phase's own "reproducible random
seeds" requirement above); metric-correctness tests against known reference values on
fixture data; graceful-failure tests (no target column selected, dataset too small, wrong
task type) that return clear errors rather than silent fabrication (matches this phase's
own "Safety" section).

## Acceptance Criteria

An end-to-end training run against a real uploaded dataset produces real, reproducible
metrics, clearly tagged as computed; failure modes are handled with clear, actionable
errors; the XGBoost decision (ADR-004) is finalized with documented evidence either way.

## Documentation Requirements

Create `../../02_DOCS/ML_SPEC.md` (approach, supported task types, metric definitions);
resolve `../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-004.

## Branch

`phase/04-ml-engine`. Child branches as needed: `backend/04-ml-engine-*`.

## Rollback Considerations

The ML module is isolated behind its own routes; revert-safe.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
