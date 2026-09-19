# Decisions Log

The full Architecture Decision Record log for this project. `ARCHITECTURE.md`'s "Decision
Log" section points here. Use [`TEMPLATE.md`](TEMPLATE.md) for new entries. Entries are
numbered sequentially and never renumbered; a superseded decision is marked as such, not
deleted.

---

# ADR-R001: Control-System Reconciliation

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** Pre-Phase-01 (reconciliation, not a build phase)

## Context
Earlier in this session, before this `00_AGENT_CONTROL/` / `01_PHASES/` / `02_DOCS/` /
`03_TEMPLATES/` structure was introduced, a standalone foundation was written directly at
the repository root: flat markdown files (`PROJECT_SPEC.md`, `ARCHITECTURE.md`,
`UI_UX_SPEC.md`, `AGENTS.md`, `PHASE_INDEX.md`, `PROGRESS.md`, `GIT_WORKFLOW.md`,
`TESTING_STRATEGY.md`, `DEVELOPMENT_RULES.md`, `docs/`), defining a **12-phase (00–11)**
roadmap and a **trunk-based** Git workflow (direct, phase-gated commits to `main`, no
mandatory branch-per-phase). It was never committed.

The human then supplied `AI_Data_Intelligence_Agent_Build_System.zip`, a separate, deliberately
prepared control system with an **8-phase (01–08)** roadmap, a `00_AGENT_CONTROL/` +
`01_PHASES/` + `02_DOCS/` + `03_TEMPLATES/` layout, and a **strict branch-per-phase** Git
workflow (`main` never touched by the agent, human-only merges). This created two
competing, incompatible control systems in the same uncommitted working tree.

## Decision
The ZIP's system is authoritative in full: its 8-phase roadmap, its folder layout, its
strict Git workflow (branch-per-phase, no direct `main` work, no agent-initiated merges).
The richer content already written in the earlier draft (detailed per-technology stack
evaluation, the full product-principles table, the complete 3D Universe UI/UX
specification, the testing methodology, and the seeded architecture decisions below) was
migrated into the ZIP's file locations rather than discarded, remapped from the old
12-phase numbering to the ZIP's 8-phase numbering. The old root-level duplicate files were
then removed once migration was verified. See the session's Foundation Review / audit /
reconciliation report for the full before/after file inventory.

## Alternatives Considered
- **Keep the 12-phase/trunk-based system, treat the ZIP as reference only** — rejected: the
  human explicitly designated the ZIP as authoritative.
- **Run both systems side by side** — rejected outright: two competing project-control
  systems is exactly the failure mode this reconciliation exists to prevent.

## Consequences
Every phase reference elsewhere in this documentation set uses the ZIP's 8-phase numbering
(`PHASE_01_FOUNDATION` … `PHASE_08_TESTING_DOCKER_DEPLOYMENT`) and its branch-per-phase Git
model. No document in this repository should reference a 9th–12th phase, a `Phase 00`, or a
trunk-based/direct-to-`main` workflow going forward — if one is found, it is a leftover from
the pre-reconciliation draft and must be fixed.

## Related
All ADRs below (renumbered phase references); `00_AGENT_CONTROL/PROJECT_STATE.md`;
`00_AGENT_CONTROL/GIT_WORKFLOW.md`.

---

# ADR-001: Frontend Stack

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION

## Context
The product's primary interface is a premium, cinematic 3D experience (the "Data
Intelligence Universe"), layered with a data-heavy 2D UI (panels, charts, tables). The
stack needs to support both without fighting itself.

## Decision
React + TypeScript + Vite + Tailwind CSS + React Three Fiber + Three.js, as proposed by the
human and the ZIP's `AGENT_MASTER_INSTRUCTIONS.md` architecture baseline.

## Alternatives Considered
- **Next.js instead of Vite** — rejected: no SSR/SEO requirement exists for a local-first,
  single-page data tool; Vite's dev loop is faster for this use case.
- **A 3D engine other than Three.js/R3F** — not seriously evaluated; R3F is the standard,
  best-supported React binding and keeps the 3D scene declarative.

## Consequences
TypeScript end-to-end (paired with Pydantic on the backend) lets the computed/AI-generated
response contract be type-checked, not just conventionally followed.

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Frontend".

---

# ADR-002: Data Visualization Library

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED — to be confirmed with real evidence in Phase 03
**Phase:** PHASE_03_DATA_PROFILING_VISUALIZATION

## Context
The product must avoid a "generic admin dashboard" look (product principle 5). Chart
library choice materially affects achievable visual identity.

## Decision
visx (Airbnb), a low-level primitives library built on D3, chosen over higher-level
pre-styled chart libraries.

## Alternatives Considered
- **Recharts** — set aside for now: fast to use, but its default visual identity is
  difficult to fully de-genericize; theming ceiling too low for the "premium" bar.
- **Nivo** — same reasoning as Recharts.
- **Observable Plot** — documented fallback if visx's lower-level API proves too slow to
  implement against in Phase 03's timeframe.

## Consequences
More implementation effort per chart than a pre-styled library, in exchange for full visual
control. If Phase 03 shows this tradeoff isn't worth it, switch to the documented fallback
and update this ADR (mark superseded, not edited in place).

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Frontend";
`../../01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`.

---

# ADR-003: Backend Stack

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION

## Context
The backend must perform real, reproducible data profiling/statistics/ML computation and
expose it over a typed API.

## Decision
Python + FastAPI + Pydantic + Pandas + NumPy + scikit-learn, as proposed by the human and
the ZIP's architecture baseline.

## Alternatives Considered
Not seriously evaluated against non-Python stacks — Python's data/ML ecosystem is the
standard, correct fit for this product's core computation needs.

## Consequences
Pydantic models become the literal mechanism enforcing the computed/AI-generated response
contract (product principle 2).

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Backend".

---

# ADR-004: XGBoost Inclusion

**Date:** 2026-09-17 (opened) / 2026-09-17 (resolved, Phase 04)
**Status:** ✅ CONFIRMED — not adopted
**Phase:** PHASE_04_ML_ENGINE

## Context
The ZIP's own Phase 04 prompt says: "Prefer scikit-learn. Use XGBoost only when it
materially adds value and is justified." Adding it means a heavier, non-sklearn-native
dependency for a niche scikit-learn's own gradient-boosting implementations may already
partially cover. Phase 00 deferred a concrete decision to this phase.

## Decision
**Not adopted.** A real benchmark was run (not a guess): `xgboost` was temporarily
installed and compared against the equivalent scikit-learn `RandomForest` estimator on
`sklearn.datasets.make_classification`/`make_regression` synthetic data (2,000 samples, 20
features, realistic noise), then uninstalled again — it is not a project dependency.

**Results:**

| Task | RandomForest | XGBoost | Delta |
|---|---|---|---|
| Classification (accuracy / F1) | 0.9025 / 0.9025 | 0.9075 / 0.9075 | +0.5pp, XGBoost slower to fit (1.88s vs 0.37s) |
| Regression (RMSE / R²) | 78.01 / 0.805 | 61.39 / 0.879 | XGBoost notably better here, and faster to fit in this run (0.08s vs 1.71s) |

The regression improvement is real and non-trivial on this synthetic benchmark. The
classification improvement is marginal. Both results are on synthetic, medium-sized data —
not the project's own local fixture datasets, which are far smaller (tens of rows), where
a complex boosting model has little room to show a genuine edge over a baseline
`RandomForest`/`Ridge`.

## Alternatives Considered
- **Adopt now, given the regression evidence** — rejected: the phase prompt is explicit
  ("Do not add a huge model zoo"), the project's own datasets are small enough that the
  observed synthetic-data advantage likely doesn't transfer, and `xgboost` is a real new
  compiled-dependency cost (packaging, install size, a second gradient-boosting
  implementation to maintain alongside scikit-learn's own). The bar in
  `AGENT_MASTER_INSTRUCTIONS.md` is "materially adds value," and a marginal-to-real but
  synthetic-only, small-dataset-irrelevant delta does not clear it convincingly enough to
  justify the dependency now.
- **Never evaluate it at all** — rejected: the phase's own Core Principle requires
  "Machine learning decisions must be transparent and reproducible," and ADR-004 explicitly
  promised a concrete evaluation, not a re-deferral.

## Consequences
`xgboost` is not a project dependency. The architecture (`app/ml/models.py`'s registry) is
explicitly designed to allow additional models later without restructuring — if a real
dataset in a later phase shows scikit-learn's baselines are insufficient, this ADR should
be superseded with fresh evidence from that actual dataset, not synthetic data.

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Backend", "Machine Learning Architecture (Phase 04)";
`../../01_PHASES/PHASE_04_ML_ENGINE/PHASE_REPORT.md`.

---

# ADR-005: Dataset & Metadata Storage

**Date:** 2026-09-17 (opened) / 2026-09-17 (resolved, Phase 02)
**Status:** ✅ CONFIRMED
**Phase:** PHASE_02_DATA_INGESTION

## Context
v1 is single-user, local-first. Uploaded files need storage; ingestion metadata needs
somewhere to live too.

## Decision
Raw files on the filesystem, under `backend/data/uploads/<dataset_id>/original.csv`
(gitignored); metadata as a JSON sidecar file, `backend/data/uploads/<dataset_id>/
metadata.json` — not a database, for v1. `dataset_id` is always server-generated (a
`uuid4`), never derived from the client's filename — this is the structural mechanism that
prevents path traversal, not a validation rule alone (`backend/app/ingestion/storage.py`).
Confirmed working at "large-ish" scale (5,000-row fixture) with no issues in Phase 02's
test suite.

## Alternatives Considered
- **SQLite via SQLAlchemy** — the natural next step if cross-dataset querying/filtering
  becomes a real requirement; a plain directory listing + per-file JSON read was
  sufficient for Phase 02's list/get endpoints at v1 scale, so this wasn't justified yet.

## Consequences
If a later phase (e.g. Phase 03's profiling results needing efficient cross-dataset
querying) finds the sidecar-file approach insufficient, this ADR is superseded by a new
one adopting SQLite, and `ARCHITECTURE.md` is updated accordingly — not silently changed
in place.

## Related
`../ARCHITECTURE.md` "Data Storage"; `01_PHASES/PHASE_02_DATA_INGESTION/PHASE_REPORT.md`.

## Related
`../ARCHITECTURE.md` "Data Storage";
`../../01_PHASES/PHASE_02_DATA_INGESTION/PHASE_PROMPT.md`.

---

# ADR-006: AI Mode Abstraction

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_05_AI_ANALYTICS

## Context
Product principles 3 and 4 (and the ZIP's own Phase 05 "Core rule": "The LLM is an
interpreter, not the source of truth") require the app to work fully without an external
LLM, and require AI output to never introduce new numeric claims.

## Decision
A pluggable AI-mode interface with an offline deterministic template-based implementation
as the default, and a real LLM provider as strictly opt-in. Every mode receives only the
already-computed JSON payload, never raw data, and is instructed to explain, not compute.

## Alternatives Considered
- **LLM-only, no offline mode** — rejected outright: directly violates principle 4 and the
  ZIP's own Phase 05 "Fallback" requirement.
- **Free-form prompting with raw data access** — rejected: cannot structurally guarantee
  principle 3; the offline-template + computed-payload-only approach can.

## Consequences
This is the concrete mechanism `../TESTING_STRATEGY.md` §6 tests against.

## Related
`../ARCHITECTURE.md` "AI Mode Abstraction";
`../../01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`.

---

# ADR-007: Real LLM Provider Choice

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED — final decision due Phase 05
**Phase:** PHASE_05_AI_ANALYTICS

## Context
The AI mode abstraction (ADR-006) needs at least one real implementation beyond the offline
default to be meaningfully "optional" rather than theoretical.

## Decision (working assumption only)
Anthropic Claude, given the project's existing tooling context — not a hard architectural
commitment, since the interface is provider-agnostic by design.

## Alternatives Considered
Not yet evaluated in depth; OpenAI/other providers remain viable given the abstraction
layer makes switching low-cost.

## Consequences
None yet — the interface does not depend on this choice.

## Related
`../ARCHITECTURE.md` "AI Mode Abstraction".

---

# ADR-008: 3D Scene State Management

**Date:** 2026-09-17 (opened) / 2026-09-18 (resolved, Phase 07)
**Status:** ✅ CONFIRMED
**Phase:** PHASE_07_3D_UNIVERSE_UI

## Context
The 3D scene has frequently-updating state (hover, selection, camera focus) that must not
cause unnecessary re-renders across the whole component tree.

## Decision
Zustand (`frontend/src/state/universeStore.ts`), chosen over React Context for its more
granular subscription model — confirmed with real implementation experience. The store holds
only interaction state (`selectedNodeId`, `hoveredNodeId`, `focusedNodeId`, `searchQuery`,
`filters`, `viewMode`); node *positions* are never store state — they're derived, pure data
from `universe/layout.ts`/`universe/mapping.ts`, recomputed via `useMemo` from already-
fetched API responses. This split (interaction state in Zustand, domain data as plain
derived data) matches this project's existing convention of never duplicating server state
in a client store (`state/DatasetSessionContext.tsx`'s same principle, Phase 06).

## Alternatives Considered
- **React Context** — set aside as a default: prone to over-rendering for
  frequently-updating state unless carefully split. Confirmed in practice: a `Search`/
  `Filters` component reading only `searchQuery`/`filters` doesn't re-render on every
  `hoverNode()` call during scene interaction, which a single Context value would not give
  for free without manual memoization.
- **Storing node positions/graph data in the store too** — rejected: it would duplicate data
  already derivable from the fetched API responses via `buildUniverseGraph()`, creating a
  second source of truth that could drift; kept as plain `useMemo`'d data in
  `UniversePage.tsx` instead.

## Consequences
Adding new interaction-state fields (e.g. a future multi-select) is a small, additive change
to `universeStore.ts`'s shape — no architectural change needed.

## Related
`../ARCHITECTURE.md` "3D Interaction & State", "Universe Architecture (Phase 07)";
`../../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md`; ADR-016.

---

# ADR-009: Infrastructure — Docker, CI, Health Checks

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION (health checks) / PHASE_08_TESTING_DOCKER_DEPLOYMENT (full Docker/CI)

## Context
`PRODUCT_SPEC.md` success criteria require a one-command local run (`docker compose up`)
and CI enforcement of the phase-gated workflow.

## Decision
Multi-stage Docker images per service, docker-compose for orchestration, GitHub Actions for
CI, `/health` endpoint(s) wired into compose health checks. A backend health endpoint is
introduced as early as Phase 01; full Docker/CI implementation is Phase 08.

## Alternatives Considered
Not seriously evaluated against alternatives — standard, low-risk infrastructure tooling
with no product-specific tradeoff to weigh.

## Consequences
None beyond the standard Docker/CI maintenance surface.

## Related
`../ARCHITECTURE.md` "Deployment Topology";
`../../01_PHASES/PHASE_01_FOUNDATION/PHASE_PROMPT.md`;
`../../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md`.

---

# ADR-010: Upload Size Limit & Supported File Type

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_02_DATA_INGESTION

## Context
`PRODUCT_SPEC.md` left the exact per-dataset size limit as an open question. Ingestion
needs a concrete, enforced number, not an indefinite "fits in memory."

## Decision
50 MB per uploaded file (`APP_MAX_UPLOAD_SIZE_BYTES`, default `52428800`), enforced after
reading the file into memory (not a streaming/early-reject check — see "Consequences"). No
separate row/column ceiling. Only `.csv` is accepted in v1, validated by extension plus a
lightweight binary-content sniff (reject files that are mostly non-printable bytes or
contain NUL bytes, even if named `.csv`) — a dependency-free mitigation for MIME/type
spoofing, per `02_DOCS/ARCHITECTURE.md` "Security & Privacy".

## Alternatives Considered
- **Streaming size rejection** (reject based on `Content-Length` before buffering the full
  body) — more robust against a genuinely hostile oversized upload, but adds complexity
  not justified for Phase 02; **explicitly deferred to Phase 08** ("Testing, Security &
  Reliability" hardening), not silently skipped.
- **A real content-type sniffing library** (e.g. `python-magic`) — rejected for now to
  avoid an extra dependency for a problem the printable-character heuristic already
  handles adequately at this phase.

## Consequences
An attacker could still send a request with a large `Content-Length` and force the server
to buffer up to just under the limit before rejection, consuming memory briefly — an
accepted, documented risk for a local-first v1, to be hardened in Phase 08.

## Related
`../ARCHITECTURE.md` "Data Storage"; `../PRODUCT_SPEC.md` "Open Questions";
`../../01_PHASES/PHASE_02_DATA_INGESTION/PHASE_REPORT.md`;
`../../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md`.

---

# ADR-011: Profiling Thresholds, Correlation & Distribution Strategy

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_03_DATA_PROFILING_VISUALIZATION

## Context
`01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md` requires deterministic
quality checks, correlation analysis, and distribution data, but leaves the exact
thresholds and statistical choices to the implementing phase — they need to be fixed,
documented constants, not ad hoc or learned values, to remain deterministic and
explainable to a future AI-explanation layer (Phase 05).

## Decision
- **Quality thresholds** (all fixed constants in `app/profiling/quality.py`): missing
  values ≥20% → warning, ≥50% → critical (dataset- and column-level); near-constant column
  at ≥95% single-value share; high-cardinality categorical at >50% unique-value ratio;
  mixed-type column at 10–90% numeric-coercible ratio; datetime detection at ≥90% parse
  success (`column_types.py`).
- **Correlation:** Pearson only, `minimum_observations` configurable (default 3), missing
  values handled pairwise per column pair, boolean columns excluded from numeric
  eligibility, an explicit `"insufficient_data"` status rather than a failure or a
  misleadingly empty success.
- **Distribution:** `numpy.histogram`, fixed default 10 bins, computed only over finite
  values; non-numeric/boolean columns and columns with no finite values are reported in
  `skipped_columns`, not force-fit into a histogram.
- **Infinite values:** excluded from descriptive statistics (min/max/mean/median/std/
  quartiles), counted separately as `infinite_count`, and raised as a `critical` quality
  finding — never allowed to propagate `inf`/`NaN` into the JSON response.
- **Storage reuse:** `app.ingestion.StorageService` gained one new public method
  (`get_raw_file_path`) rather than profiling building its own storage layer, per the
  phase prompt's explicit "do not create a second incompatible dataset storage system."

## Alternatives Considered
- **Learned/adaptive thresholds** (e.g. IQR-based outlier-style thresholds per dataset) —
  rejected: violates "deterministic computation is the source of truth" in spirit, since
  the *threshold itself* would then depend on the data being evaluated, making results
  harder to explain consistently across datasets. Fixed, documented constants were chosen
  instead.
- **Dataset-wide `dropna()` for correlation** — rejected: would discard entire rows for a
  column pair even when other pairs don't need to, reducing usable observations
  unnecessarily.
- **A larger or dataset-size-relative bin count for histograms** — rejected for v1
  simplicity; a fixed default is easier to reason about and test; revisit if real-world
  datasets show it's inadequate.

## Consequences
Every threshold above is a named constant in the relevant module, cross-referenced from
this ADR — a future phase (or a human) adjusting one should update both the constant and
this record, not just the code.

## Related
`../ARCHITECTURE.md` "Profiling Architecture (Phase 03)";
`../../01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_REPORT.md`.

---

# ADR-013: ML Engine Architecture — Model Set, Preprocessing, Train+Evaluate Merge

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_04_ML_ENGINE

## Context
`01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md` requires a small, transparent baseline ML
engine with deterministic task detection, leakage-safe preprocessing, and an API exposing
"train baseline model" and "evaluate model" as (seemingly) separate operations, alongside
"validate target" and "compare baseline models."

## Decision

- **Model set (fixed, small):** `LogisticRegression` + `RandomForestClassifier` for
  classification; `LinearRegression` + `Ridge` + `RandomForestRegressor` for regression.
  XGBoost evaluated and not adopted (ADR-004).
- **Preprocessing:** a single `sklearn.compose.ColumnTransformer` — numeric features get
  median imputation + standard scaling; categorical (including boolean) features get
  most-frequent imputation + one-hot encoding with unseen categories ignored at transform
  time. Free-text, datetime, and semantically-unknown columns are excluded from features
  outright (reported in `excluded_columns` with a reason), not force-encoded. This reuses
  Phase 03's `detect_semantic_type` rather than re-implementing column-type logic.
- **Leakage prevention, structurally enforced:** the train/test split happens once, before
  any preprocessing is fit; each model's `Pipeline` (preprocessing + estimator) is fit only
  on the training split, `.predict()` reuses already-fitted parameters on the test split.
  A feature column that is an exact duplicate of the target is detected and excluded
  (`duplicate_of_target`). Constant columns (zero variance) are excluded. Infinite values
  are replaced with `NaN` before imputation rather than crashing the pipeline.
- **"Train" and "evaluate" are merged into one atomic operation** (`POST .../ml/train`):
  since this project has no model persistence/serving layer (explicitly out of scope —
  "Do not introduce ... model serving infrastructure"), there is nothing to "evaluate"
  later that isn't produced by training itself. A separate stateful "evaluate a previously
  trained model" endpoint would require persisting fitted model objects between requests,
  which is real infrastructure this phase deliberately does not build.
- **Task-feasibility counts non-null target rows, not raw dataset rows:** a row with a
  missing target can never be used for supervised training regardless of how many rows the
  dataset has overall — `MIN_ROWS_FOR_TRAINING` (10) and all cardinality checks apply to
  the *non-null* target count.
- **Metrics use `average="weighted"`** for precision/recall/F1 uniformly across binary and
  multiclass classification, rather than branching on `pos_label` for binary — simpler,
  still valid, and avoids an arbitrary "positive class" assumption for arbitrary string
  labels.
- **ROC-AUC** is computed only for binary classification with available predicted
  probabilities; multiclass and probability-less models report it in `unavailable_metrics`
  with a reason, never a fabricated or misleading value.
- **`scipy==1.14.1` pinned** alongside `scikit-learn==1.5.2`: the newest available `scipy`
  (1.18.1) triggered a real `OptimizeWarning` from `LogisticRegression`'s lbfgs solver
  passing a solver option newer `scipy` no longer recognizes — a genuine version-skew
  issue, not a false positive. Pinning to a `scipy` version contemporaneous with this
  `scikit-learn` release resolved it cleanly (verified: zero warnings under
  `warnings.simplefilter("error")`).

## Alternatives Considered
- **A larger model zoo** (SVM, KNN, gradient boosting variants) — rejected per the phase
  prompt's explicit "Do not add a huge model zoo."
- **Per-model-type preprocessing** (e.g. skip scaling for tree-based models) — rejected for
  simplicity; scaling numeric features doesn't hurt tree-based models' accuracy (they're
  invariant to monotonic per-feature scaling), so one shared pipeline is simpler and still
  correct for every model in the registry.
- **A stateful train → store → evaluate-later flow** — rejected; see "Train/evaluate
  merge" above.

## Consequences
Adding a genuinely new task-specific evaluate step later (e.g. cross-validation, a
held-out validation set distinct from train/test) is a natural, additive extension of
`app/ml/training.py` without needing to revisit this decision.

## Related
`../ARCHITECTURE.md` "Machine Learning Architecture (Phase 04)"; ADR-004;
`../../01_PHASES/PHASE_04_ML_ENGINE/PHASE_REPORT.md`.

---

# ADR-014: AI Provider Abstraction, Grounding Guarantee, No-Silent-Fallback

**Date:** 2026-09-18
**Status:** ✅ CONFIRMED
**Phase:** PHASE_05_AI_ANALYTICS

## Context
`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` requires an optional AI layer that can
never invent dataset facts, must not hard-code to one AI vendor, must degrade gracefully
with zero configuration, and must defend against prompt injection from dataset content.
`ARCHITECTURE.md`'s pre-existing "AI Mode Abstraction" section had already committed to a
provider-style interface with an offline default; this phase had to pick and implement the
real provider, and design the mechanism that makes the "never invent a fact" requirement
an enforced guarantee rather than a prompting convention.

## Decision

- **Provider interface (`app/ai/provider.py`):** an `AIProvider` ABC with `is_available()`
  and `generate(system_instructions, evidence, user_request) -> ProviderResult`. A provider
  receives only the already-built, size-bounded evidence dict — never raw dataset rows,
  never application configuration/secrets — and returns narrative text only.
- **Two providers, selected by `APP_AI_PROVIDER` (`offline` default / `anthropic` /
  `disabled`), no silent fallback:** if `anthropic` is configured without an API key, the
  factory still returns an `AnthropicProvider` instance whose own `is_available()` reports
  the misconfiguration honestly — it never silently substitutes `OfflineProvider`. Silent
  fallback would make a broken configuration look like a working one.
- **Real provider = Anthropic's Messages API via direct `httpx.post`, not an SDK:** per the
  phase prompt's "Dependency Discipline" ("Do not add a large AI framework merely for
  convenience"). `httpx` is already a project dependency (the FastAPI test client has used
  it since Phase 01); a single REST endpoint needs nothing more. Every failure mode
  (timeout, network error, 401, 429, other 4xx/5xx, malformed JSON body) is caught and
  re-raised as a structured `AIError`, never a raw `httpx` exception reaching the API layer.
- **The Grounding Guarantee, enforced structurally:** `computed` is built from deterministic
  evidence (`evidence.py`, reusing Phase 02-04's own already-computed output) *before*
  `provider.generate()` is ever called, and is returned unmodified afterward. A provider has
  no parameter or return path that could alter it — only `ai_explanation.text` reflects
  whatever the provider produced. Proven, not just asserted: `tests/test_ai_grounding.py`
  uses a `FakeProvider` that returns deliberately fabricated/wrong text (wrong row count,
  wrong mean, wrong correlation, wrong ML metric, wrong duplicate count) and asserts
  `computed` is exactly correct in every case regardless.
- **Deterministic-first question routing (`routing.py`):** a fixed set of recognized
  question patterns resolve directly from Phase 02-04 output before any provider is
  consulted, rather than asking an LLM to compute a number it could get wrong. Column-name
  matching uses word-boundary regex (`\bcolumn_name\b`), not a substring check — a real bug
  caught during this phase's own testing: a naive substring check let "age" match inside
  "average", producing a false-positive resolved answer for a question about a
  nonexistent column.
- **Prompt injection defense is structural, not just instructional:** evidence is always
  wrapped as a clearly delimited, explicitly-labeled "untrusted data" JSON block
  (`security.py`'s `build_user_prompt`), with system instructions establishing that
  hierarchy for the real provider. The offline provider is additionally immune by
  construction — it only ever substitutes named fields into fixed templates, with no
  "interpretation" step where a string could be mistaken for an instruction.
- **Data minimization:** evidence size is capped (`MAX_SUMMARY_COLUMNS=30`,
  `MAX_QUALITY_FINDINGS=20`, `MAX_CORRELATION_PAIRS=10`, plus Phase 03's existing ≤5 sample
  values) — raw dataset rows are never sent to any provider.
- **Secret handling:** the API key is a Pydantic `SecretStr` on `Settings`, used only in the
  `x-api-key` HTTP header — never in a request body, never logged, and no response schema
  has a field that could echo it back.

## Alternatives Considered
- **A single hard-coded Anthropic integration with no abstraction** — rejected; the phase
  prompt explicitly requires vendor-agnosticism, and the offline provider (required outright
  for principle 4) already forces an interface to exist regardless.
- **Silently falling back to the offline provider when `anthropic` is misconfigured** —
  rejected; this would hide a configuration error behind output that looks identical to a
  deliberately offline-mode response, making misconfiguration invisible.
- **An official Anthropic SDK dependency** — rejected per "Dependency Discipline"; a single
  REST endpoint over already-present `httpx` is simpler and has one fewer dependency to
  track.
- **Prompting alone as the grounding mechanism** ("tell the model not to invent numbers") —
  rejected as the *sole* mechanism; kept as a defense-in-depth layer (`SYSTEM_INSTRUCTIONS`)
  but not relied upon, since an LLM's own text has no way to reach or alter `computed`
  regardless of what it says.

## Consequences
Adding a third provider (a different vendor, or a local model) is a natural, additive
extension: implement `AIProvider`, add a branch in `factory.py`, no change to `service.py`,
`evidence.py`, or the grounding mechanism. The grounding guarantee is a property of the
architecture (evidence built before the provider is called, provider returns text only),
not of any individual provider's behavior — so it holds automatically for any future
provider without additional enforcement code.

## Related
`../ARCHITECTURE.md` "AI Analytics Architecture (Phase 05)", "The Grounding Guarantee";
`../../01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_REPORT.md`; `tests/test_ai_grounding.py`;
`tests/test_ai_security.py`.

---

# ADR-015: Frontend Integration Architecture — Routing, Charts, State

**Date:** 2026-09-18
**Status:** ✅ CONFIRMED
**Phase:** PHASE_06_API_FRONTEND_INTEGRATION

## Context
`01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md` requires wiring the full
Phase 02-05 backend into a real 2D application (route structure, typed API client,
loading/error/empty states, caching/state strategy "where justified") while
`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md`'s dependency-addition policy requires a
recorded reason for every new dependency. `ARCHITECTURE.md`'s Phase 00 stack evaluation
had left the frontend data-visualization library as 🟡 ASSUMED (**visx**), "revisit in
Phase 03" — Phase 03 was backend-only (no frontend chart work happened then, per its own
phase boundary), so that decision was actually still open going into this phase.

## Decision

- **Routing: `react-router-dom` (v7, declarative API only — `BrowserRouter`/`Routes`/
  `Route`/`NavLink`/`useParams`/`useOutletContext`).** The standard, well-supported choice
  for a React SPA; the phase prompt explicitly asks for a real route structure (landing →
  dataset workspace → per-capability tabs) and the project had no routing library yet. Its
  newer data-router/loader API was deliberately not adopted — the phase prompt also says
  "do not over-engineer routing," and every data need here is already served by the
  existing typed API client plus `useAsync`/`useLazyAsync` hooks (below).
- **Charts: hand-rolled SVG components (`frontend/src/viz/`), no charting dependency.**
  Supersedes the Phase 00 visx assumption. Every chart this phase needs — a fixed-bin
  histogram, a single correlation-magnitude bar, a categorical frequency list — is a small,
  fixed shape driven entirely by data the backend already bins/computes (`numpy.histogram`
  server-side, Pearson coefficients server-side). A general-purpose charting library's
  value is in handling chart types, scales, and interactions this project doesn't need yet;
  paying that dependency cost now, before Phase 07's real visual-identity pass, isn't
  justified. Revisit if Phase 07 needs chart types this approach can't reasonably cover.
- **State: no state-management library.** Server data is fetched via two small hooks
  (`useAsync` for mount-time loads, `useLazyAsync` for user-triggered actions) that wrap
  the typed API client — not a query/cache library (e.g. TanStack Query). The one piece of
  genuine client-only state (the last trained `ModelResult`, needed by the AI
  `ml_explanation` capability since the backend has no model-persistence layer, ADR-013)
  lives in a single small React Context (`state/DatasetSessionContext.tsx`), scoped to one
  dataset's workspace. This matches the phase prompt's own "use the simplest appropriate
  state architecture" instruction — there is no cross-dataset shared cache, background
  refetching, or optimistic-update requirement that would justify a dedicated library.
- **API client stays hand-written TypeScript, not OpenAPI-codegen.** `types.ts` mirrors the
  backend's actual Pydantic schemas field-for-field (verified against the schema source
  files directly, not guessed), organized as one interface per response model plus
  capability-specific "evidence" interfaces for the AI layer's `computed` field (which is
  intentionally an open dict server-side, since it varies per AI capability — see
  `backend/app/ai/evidence.py`). A codegen tool was considered but rejected for this phase:
  it would add a devDependency and a generated-file question (checked in vs. build step)
  for a schema surface that's small enough to keep in sync by hand, verified against a real
  running backend as part of this phase's own runtime verification.

## Alternatives Considered
- **TanStack Query** — rejected; no requirement here (background refetch, cross-component
  cache sharing, pagination) that a plain `useEffect`-based hook doesn't already satisfy,
  and it would be a second data-fetching pattern alongside the typed API client rather than
  a replacement for one.
- **Zustand/Redux** — rejected for the same reason `ARCHITECTURE.md`'s "3D Interaction &
  State" section defers Zustand to Phase 07 (a frequently-updating 3D scene): this phase's
  state is simple, low-frequency, and scoped to a single dataset session.
- **visx / Observable Plot** — visx (the original assumption) was not adopted per the
  reasoning above; Observable Plot (`ARCHITECTURE.md`'s own documented fallback) was also
  not needed for the same reason — this phase's chart requirements turned out to be small
  and fixed-shape once actually known, which is exactly the condition `ARCHITECTURE.md`
  flagged for revisiting the choice.
- **openapi-typescript codegen** — rejected for now per the reasoning above; worth
  revisiting if the API surface grows enough that manual sync becomes error-prone (a real
  risk future phases should watch for, not a closed question).

## Consequences
Adding a real chart type Phase 07 needs but this approach can't reasonably produce (e.g. a
force-directed graph layout for the 3D Universe's 2D fallback) is an explicit, justified
reason to add a charting dependency then, with its own ADR — not a retroactive judgment
that this decision was wrong for Phase 06's actual, smaller requirements. Similarly, if the
API surface grows substantially, introducing `openapi-typescript` (or regenerating a
snapshot as part of CI) is a natural, additive change to `api-client/`, not a rewrite.

## Related
`../ARCHITECTURE.md` "Stack Evaluation" → "Frontend" (visx entry, superseded here),
"Module Boundaries"; `../../01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_REPORT.md`;
`frontend/src/api-client/`, `frontend/src/viz/`, `frontend/src/state/`.

---

# ADR-016: Universe Node Taxonomy, Visual Encoding, Layout & Performance Tiers

**Date:** 2026-09-18
**Status:** ✅ CONFIRMED
**Phase:** PHASE_07_3D_UNIVERSE_UI

## Context
`01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md` and `02_DOCS/UI_UX_SPEC.md` §4 specify
the Universe's *minimum* node taxonomy (dataset + 6 domain nodes) and require every visual
encoding to be fixed and documented, but leave the concrete hierarchy depth, exact visual
mappings, layout algorithm, and performance-tier thresholds to this phase, per §9's open
questions. The conversation's own Phase 07 brief additionally asked for a deeper 4-level
hierarchy (dataset → domains → features → relationships), search, filters, and a legend —
consistent with, and a superset of, `UI_UX_SPEC.md`'s confirmed minimum, not a conflict.

## Decision

- **5 domain nodes, not 6:** Profile, Quality, Analytics, ML, AI. `UI_UX_SPEC.md`'s original
  list separated "Statistics" and "Visualization," but Phase 06 already merged both into one
  `AnalyticsPage` (correlation + distribution) — there is no second, distinct backend
  capability to justify a second 3D node, and a duplicate/empty node would itself violate
  principle 6 ("no unnecessary 3D objects"). Documented as a deviation in `UI_UX_SPEC.md`
  §4.1, not a silent change.
- **Feature nodes populate progressively, not all at once:** one ring per domain (Profile,
  Analytics), appearing only once that domain node is focused/selected, capped at
  `PROFILE_FEATURE_CAP=60` / `ANALYTICS_PAIR_CAP=30` correlation pairs
  (`universe/mapping.ts`). This is the large-dataset handling strategy (phase brief §11) —
  simpler than clustering/LOD, and the 2D fallback's search/table remains the uncapped,
  complete view for any dataset with more columns than the cap.
- **Fixed visual encodings, one meaning per property, documented in-app (`Legend.tsx`) and
  in code (`universe/sceneTokens.ts`):**
  - Feature-node **color** → `semantic_type` (numeric/categorical/boolean/datetime/text/
    unknown), one swatch each.
  - Feature-node **size** → normalized missingness (`null_percentage`) — the single size
    meaning; no second, conflicting property ever drives size.
  - Correlation-edge **thickness** → normalized `|coefficient|`; **color** → sign (never
    implies causation — every label says "correlation").
  - The **secondary accent** (violet) is reserved exclusively for AI-sourced content (the
    AI domain node, `AIInsightPanel`, `AIExplanationBlock`) — never used for deterministic
    data, making principle 2's computed-vs-AI-generated separation visible spatially.
- **Deterministic layout, no `Math.random()`:** domain-node positions are a fixed function
  of a constant ordering (no seed needed — they never depend on data); feature-ring
  positions use a golden-angle "sunflower" spiral rotated by a per-dataset deterministic
  seed (FNV-1a hash of `dataset_id` + domain, fed into a mulberry32 PRNG step) — the same
  dataset always renders identically; different datasets look visually distinct.
- **Performance tiers, concrete thresholds (`universe/tiers.ts`):** no-WebGL or viewport
  <768px → 2D fallback only (Canvas never mounts); 768–1279px viewport or
  `hardwareConcurrency` ≤4 → mid tier (30-node cap, no fog/starfield); ≥1280px and capable →
  high tier (60-node cap, starfield + fog). No post-processing library at any tier — "glow"
  comes from `meshStandardMaterial` emissive intensity alone.
- **No per-frame animated connection "flow":** dashed static lines instead of an animated
  dash-offset, per the phase's own "Performance" priority outweighing a purely decorative
  effect; hover/selection highlighting already communicates "this connection is real."
- **Correlation edges are not individually clickable in 3D:** thin-line raycasting at
  distance is an unreliable click target; the Analytics domain node's 2D panel
  (`panels/CorrelationPanel.tsx`) gives the identical pairs/coefficients precisely instead —
  a direct application of "3D for spatial context, 2D for precision," not a gap. This also
  meant ADR-015's anticipated "force-directed graph layout for the 2D fallback" never
  materialized as a real need — a plain table/list was sufficient once the actual
  requirement (search + exact values) was known, so no charting dependency was added.
- **Universe tab, not a route replacement:** added as a new first tab
  (`/datasets/:id/universe`) in `WorkspaceLayout`, not a replacement of the Overview index
  route — every Phase 06 route/test stays unchanged (see `ARCHITECTURE.md` "Universe
  Architecture (Phase 07)").
- **Code-split via `React.lazy`:** three.js/R3F/drei only load when the Universe tab is
  opened — confirmed by a measured build-size drop (main bundle ~1.26 MB → ~215 KB, Universe
  chunk ~1.05 MB loaded on demand), not a guess.

## Alternatives Considered
- **Render every feature node and every correlation pair unconditionally** — rejected: for
  a wide dataset this is exactly the "hundreds/thousands of unnecessary 3D objects" the
  phase brief warns against; progressive disclosure + caps were chosen instead.
- **A learned/heatmap-style correlation color gradient** — rejected: a single Pearson
  coefficient doesn't carry enough precision to justify a gradient implying more nuance than
  the number has; a two-color sign encoding plus the exact number in the 2D panel is honest
  about what the statistic actually says.
- **`@react-three/postprocessing` for bloom** — rejected: the phase brief explicitly says
  heavy post-processing isn't used by default at any tier; emissive materials achieve a
  "premium glow" look without the dependency or the runtime cost.
- **Zustand-stored node positions** — rejected; see ADR-008.

## Consequences
Every visual encoding is a named constant in `universe/sceneTokens.ts`/`universe/mapping.ts`,
cross-referenced from this ADR and from the in-app `Legend` — a future phase or a human
adjusting one should update the constant, the Legend copy, and this record together, not
just the code (mirrors the pattern ADR-011 established for profiling thresholds).

## Related
`../ARCHITECTURE.md` "Universe Architecture (Phase 07)"; `../UI_UX_SPEC.md` §4, §9;
`../../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md`;
`../../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_REPORT.md`; ADR-008; ADR-015.

---

# ADR-017: Phase 08 Docker/CI Execution — Concrete Choices

**Date:** 2026-09-18
**Status:** ✅ CONFIRMED
**Phase:** PHASE_08_FINAL_PRODUCTIZATION_RELEASE

## Context
ADR-009 pre-committed to "multi-stage Docker images per service, docker-compose for
orchestration, GitHub Actions for CI, `/health` wired into compose health checks" without
fixing the concrete implementation. This phase implements it and records the choices ADR-009
left open.

## Decision
- **Backend image:** `python:3.12-slim` two-stage build (a `build-essential` builder stage
  compiles any wheel without a prebuilt binary for the target platform; the runtime stage
  has no compiler at all), pinned exactly to `backend/requirements.txt`, runs as a
  non-root `app` user, `HEALTHCHECK` calls `/health` via `urllib` (no extra `curl`
  dependency installed just for the check).
- **Frontend image:** `node:20-slim` builds the Vite production bundle; served by
  `nginxinc/nginx-unprivileged:1.27-alpine` (not plain `nginx:alpine`) specifically so the
  container runs as non-root without extra `USER`/permission plumbing — it already listens
  on 8080 unprivileged. `nginx.conf` adds the SPA fallback (`try_files ... /index.html`,
  required for `react-router-dom` deep links to survive a hard refresh) and long-cache
  headers for hashed `dist/assets/*` only, never for `index.html` itself.
- **Compose networking:** the frontend is a static SPA — the *browser*, not the nginx
  container, calls the backend directly, so there is no container-to-container API proxy.
  `VITE_API_BASE_URL` is a frontend **build arg** (Vite inlines `VITE_*` vars at build time;
  there is no runtime env-var injection point in a static bundle), defaulting to
  `http://localhost:8000` to match the default `BACKEND_PORT`.
- **Persistence:** a named volume (`backend-data`) mounted at `/app/data`, not a bind mount —
  uploaded datasets survive `docker compose down`/`up` without depending on host path
  conventions, consistent with `StorageService`'s existing filesystem-only design (ADR-005).
- **Root `.env.example`:** documents Compose-level overrides (ports, AI provider pass-
  through, the frontend build arg) separately from `backend/.env.example` /
  `frontend/.env.example`, which remain for non-Docker local development.
- **CI (`​.github/workflows/ci.yml`):** three jobs — `backend` (ruff + pytest),
  `frontend` (eslint + vitest + `tsc`+build), `docker` (depends on both passing first,
  then `docker compose up -d --build`, polls the backend's health status, curls both
  services, always dumps logs and tears down). Replaces a stray, unrelated
  `python-publish.yml` (a default GitHub-template PyPI-publish workflow, never applicable
  to this project — dead CI debris removed as part of this phase's cleanup pass).
- **Known limitation, honestly recorded, not hidden (per this phase's own "No Fake
  Completeness" rule):** Docker is not installed in the agent's execution environment for
  this phase, so the images could not be locally build- or runtime-verified here. Every
  Dockerfile/compose line was manually re-checked for correctness, and the backend was
  smoke-tested locally under the exact non-reload `uvicorn` invocation the Dockerfile's
  `CMD` uses (`/health` returned 200). The `docker` CI job above will perform the first
  actual build+runtime verification, on GitHub Actions' Docker-equipped runners, the first
  time this branch's CI runs — that CI result, not this document, is the real verification
  and should be checked before treating Docker support as proven.

## Alternatives Considered
- **`nginx:alpine` + manual `USER`/chown plumbing** — rejected: `nginx-unprivileged` is a
  maintained image that solves exactly this with less custom Dockerfile logic.
- **Bind-mounting `backend/data/uploads` from the host** — rejected: couples the container
  to a host directory layout for no benefit `docker-compose`'s own named volumes don't
  already provide.
- **A reverse-proxy container in front of both services** — rejected as unnecessary
  complexity for a local-first, single-user tool; would be reconsidered for a real public
  deployment, which remains explicitly out of scope (`PRODUCT_SPEC.md` "Non-Goals").

## Consequences
Anyone running `docker compose up --build` gets a working stack with zero required
configuration, matching the non-Docker local-dev experience's "zero required config"
principle. Changing the backend's published port requires also updating
`VITE_API_BASE_URL` (documented inline in `.env.example`), since it is baked in at frontend
build time, not at container start time — a real constraint of static SPAs, not an
oversight.

## Related
`../ARCHITECTURE.md` "Deployment Topology"; ADR-005; ADR-009;
`../../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md`; `../SECURITY_NOTES.md`.

---

# ADR-018: Dataset-ID Path-Traversal Hardening

**Date:** 2026-09-18
**Status:** ✅ CONFIRMED
**Phase:** PHASE_08_FINAL_PRODUCTIZATION_RELEASE

## Context
`app/ingestion/storage.py`'s own docstring (Phase 02) claimed path traversal was
structurally impossible because `dataset_id` is "always server-generated, never derived
from client input." That claim was only true for the *write* path (`POST /datasets`,
which does generate the id server-side via `uuid4()`). Every *read* path
(`GET /datasets/{dataset_id}`, and every profiling/ML/AI endpoint nested under
`/datasets/{dataset_id}/...`) takes `dataset_id` straight from the URL — client-controlled
— and joined it directly onto `base_dir` with no format check. `pathlib` does not collapse
`..` segments itself, but the OS resolves them at the syscall level
(`Path.exists()`/`open()`), so a `dataset_id` such as `..\\some-other-dir` (backslash is
not a URL path separator, so it reaches the `{dataset_id}` route parameter unmodified,
unlike a literal `/`) is a real path-traversal primitive, not a theoretical one — confirmed
empirically with `fastapi.testclient.TestClient` against a real target directory placed
just outside the isolated test storage root before the fix, and disproven the same way
after it.

## Decision
`StorageService._dataset_dir` now rejects any `dataset_id` containing anything other than
letters, digits, hyphens, or underscores — every real id (`str(uuid4())`) always matches;
`/`, `\`, and `.` (so also `..`) never do — and returns `None` before any filesystem call is
made, which every existing caller (`read_metadata`, `get_raw_file_path`) already treated as
"dataset not found," so no call site changed and the public 404 contract is unchanged. A
character allowlist was chosen over a strict UUID4-shape regex specifically so it doesn't
also break `StorageService`'s own existing unit tests, which legitimately construct
`StorageService` directly with simple test ids like `"ds1"` (bypassing the API layer
entirely) — the allowlist still makes traversal structurally impossible while not
over-constraining what counts as a valid id at the storage layer. Regression tests added in
`tests/test_datasets_api.py::TestDatasetIdTraversal` (HTTP-level, via the real route) and
directly against `StorageService` (unit-level).

## Alternatives Considered
- **Validate at the router layer instead of `StorageService`** — rejected: would need
  duplicating the same check in `datasets.py`, `profile.py`, `ml.py`, and `ai.py`
  independently, and any future endpoint taking `dataset_id` would silently lack the
  guard unless someone remembered to add it. Fixing it once in the single function every
  one of them already funnels through is structural, not a convention someone can forget.
- **Strict UUID4 regex** — rejected after it broke 4 existing loader unit tests that use
  non-UUID test ids; the character-allowlist approach blocks the same attack surface
  (no separators, no dots, ever) without that collateral damage.

## Consequences
None for legitimate use — every id the application itself ever generates already matches
the allowlist. Any future code that calls `StorageService` with a non-conforming id will now
get a `None` (read paths) or a raised `ValueError` (write paths, which should never receive
a non-server-generated id in the first place) instead of silently succeeding.

## Related
`../SECURITY_NOTES.md`; `app/ingestion/storage.py`;
`tests/test_datasets_api.py::TestDatasetIdTraversal`.

---

# ADR-019: Desktop-Scaling Layout & App-Wide Focus States

**Date:** 2026-09-19
**Status:** ✅ CONFIRMED
**Phase:** PHASE_08_FINAL_PRODUCTIZATION_RELEASE (desktop-focused follow-up pass)

## Context
`UI_UX_SPEC.md` §6 said "desktop is the primary target" since Phase 01, but
`WorkspaceLayout.tsx` capped every workspace page — including the 3D Universe — at a fixed
`max-w-5xl` (1024px) regardless of monitor size. Verified live by resizing a real browser
through 1280×720 up to 3840×2160: on a 1440p/4K display the Universe (the product's flagship
visualization) rendered no larger than on a 1280px laptop, with the difference spent
entirely as dead side margin — the exact "excessive empty space on large displays" failure
mode. Separately, no interactive element anywhere in the app had an explicit focus style;
nothing suppressed the browser default, but nothing styled it either, which is inconsistent
with the app's otherwise deliberate dark visual system.

## Decision
- **Universe route:** no content max-width — `max-w-none` with responsive padding
  (`px-6 md:px-10 2xl:px-16`), so the canvas scales continuously with the viewport. A fixed
  1800px cap was tried first and rejected after the live 2560px/4K check showed it was still
  too conservative.
- **All other workspace routes:** kept a capped reading width, but wider than before —
  `max-w-6xl` (1152px), `max-w-[1400px]` from `2xl` up — a deliberate readability choice for
  text/list/table content, not the same treatment as the canvas.
- `AnalyticsPage`'s distribution grid gained `xl:grid-cols-3` (was fixed at 2 columns) to use
  extra width for more visible histograms rather than just whitespace.
- Added one global `@layer base` rule in `index.css` giving every interactive element a
  consistent `focus-visible` ring in the existing `accent` token, rather than touching every
  individual button/link's className across the codebase.

## Alternatives Considered
- **A single wider fixed cap for all pages (including Universe)** — rejected: a fixed pixel
  number that looks right at 1920px either wastes space at 4K or (if sized for 4K) looks
  arbitrary/too-wide at 1366px; a canvas has no comparable readability ceiling a text column
  has, so removing the cap entirely for that one route is the more correct fix, not a
  compromise.
- **Per-component focus styles instead of a global rule** — rejected as needless repetition
  across dozens of buttons/links with no behavioral difference from one shared rule.

## Consequences
None negative found; verified with the full frontend suite (131/131 tests, lint, typecheck,
build all clean) and a live interaction pass (orbit/zoom/click-to-select/hover/Escape/Reset
View/search-to-focus all confirmed working at 1920×1080 after the change).

## Related
`../UI_UX_SPEC.md` §5, §6; `frontend/src/features/workspace/WorkspaceLayout.tsx`;
`frontend/src/index.css`; `frontend/src/features/analytics/AnalyticsPage.tsx`.
