# Architecture

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED

```text
React + TypeScript
      |
      | typed HTTP/API
      v
FastAPI
      |
      +--> Ingestion
      +--> Profiling / Statistics
      +--> Visualization Data
      +--> ML Engine
      +--> AI Context + Explanation
```

The 3D UI consumes structured outputs from the backend and remains a presentation layer.
Business logic must never live inside UI components
(`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md`, "Separation of concerns").

## Stack Evaluation

The proposed stack was evaluated rather than accepted by default, per
`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md` ("Do not add a technology merely because it
is fashionable"). Every dependency added beyond this baseline needs its own entry in
[`decisions/DECISIONS_LOG.md`](decisions/DECISIONS_LOG.md).

### Frontend

| Technology | Decision | Status | Rationale |
|---|---|---|---|
| React + TypeScript | Adopted | ✅ CONFIRMED | Right default for a component-heavy, stateful, long-lived app; TypeScript keeps the computed/AI-generated data contract type-safe end-to-end. |
| Vite | Adopted | ✅ CONFIRMED | Fast dev loop, first-class React+TS template; no SSR/SEO requirement exists for this single-page tool. |
| Tailwind CSS | Adopted | ✅ CONFIRMED | Fast, consistent utility styling for the 2D chrome; keeps the design-token system (`UI_UX_SPEC.md`) centralized. |
| React Three Fiber + Three.js | Adopted | ✅ CONFIRMED | The Universe is not optional — it's the product's primary interface. R3F is the standard, well-maintained React binding, keeping the 3D scene declarative and testable at the state level. `@react-three/drei` is the standard helper library — ✅ CONFIRMED (Phase 07): `CameraControls` (camera focus/reset/zoom clamps), `Html` (billboard node labels), `Line` (dashed connection/correlation edges), `Stars` (high-tier atmosphere). No `@react-three/postprocessing` was added — see "Universe Architecture (Phase 07)". |
| Data visualization library | **Hand-rolled SVG** (`frontend/src/viz/`), no charting dependency | ✅ CONFIRMED (Phase 06, supersedes the earlier visx assumption) | Phase 03 (backend-only) never actually exercised this decision, so it was still open going into Phase 06. Once real requirements were known (a fixed-bin histogram, a correlation-magnitude bar, a categorical frequency list — all driven by data the backend already computes/bins), they turned out small and fixed-shape enough that a general-purpose charting library's value (chart types, scales, interactions) wasn't needed. See ADR-015. Revisit if Phase 07 needs chart types this doesn't reasonably cover. |

### Backend

| Technology | Decision | Status | Rationale |
|---|---|---|---|
| Python + FastAPI | Adopted | ✅ CONFIRMED | Async-capable, Pydantic-native (schema = validation = OpenAPI docs in one place). |
| Pydantic | Adopted | ✅ CONFIRMED | Single source of truth for API schemas, including the computed/AI-generated envelope — this enforces principle 2 at the type level, not just by convention. |
| Pandas + NumPy | Adopted | ✅ CONFIRMED | Standard, correct choice for profiling/statistics on in-memory tabular data. |
| scikit-learn | Adopted | ✅ CONFIRMED | Baseline, interpretable models fit a "baseline ML" feature (AutoML/deep learning are non-goals). |
| XGBoost | **Conditional** | 🟡 ASSUMED (deferred) | Not adopted outright — adds a heavier, non-sklearn-native dependency for gains that scikit-learn's own gradient-boosting implementations may already cover for baseline tabular tasks. **Phase 04 must evaluate it concretely** (accuracy delta on real fixture datasets vs. dependency cost) and record a final decision in `decisions/DECISIONS_LOG.md`. Not installed until then. |

### Data Storage

| Concern | Decision | Status | Rationale |
|---|---|---|---|
| Uploaded dataset files | Filesystem, under `backend/data/uploads/<dataset_id>/original.csv` (gitignored) | ✅ CONFIRMED (Phase 02) | Simplest correct option for a local-first, single-user v1; avoids a database dependency for raw file bytes. `dataset_id` is always server-generated (never derived from the client's filename), which is what structurally prevents path traversal — see `app/ingestion/storage.py`. |
| Dataset metadata | JSON sidecar file per dataset, `backend/data/uploads/<dataset_id>/metadata.json` — **not** a database | ✅ CONFIRMED (Phase 02) | Implemented and load-tested at "large-ish" scale (5,000 rows) in Phase 02 without issue. A directory listing + per-file JSON read is sufficient for list/get at single-workspace v1 scale. Revisit with a real ADR if cross-dataset querying/filtering becomes a genuine requirement (e.g. Phase 03+ needs to filter/sort across many datasets) — not yet justified. |
| Max upload size | 50 MB per file (`APP_MAX_UPLOAD_SIZE_BYTES`, default `52428800`) | ✅ CONFIRMED (Phase 02) | Resolves the `02_DOCS/PRODUCT_SPEC.md` open question. Chosen to comfortably cover realistic CSV datasets for a portfolio-scale demo while staying well within "fits in memory on a single developer machine." No separate row/column ceiling is enforced in v1 — it's implicitly bounded by this byte cap plus in-memory `pandas` parsing (no streaming/chunked ingestion yet). Revisit if a real dataset hits this ceiling. |
| Supported file type | `.csv` only for v1 (validated by extension; content is also sniffed to reject binary files disguised with a `.csv` extension) | ✅ CONFIRMED (Phase 02) | Matches `02_DOCS/PRODUCT_SPEC.md` "Input" (CSV initially); JSON/Parquet remain a documented future possibility, not built. |

### 3D Interaction & State

- ✅ CONFIRMED (Phase 07) — 3D scene *interaction* state (selection, hover, focus, search,
  filters, view mode) is managed in `frontend/src/state/universeStore.ts`, a **Zustand**
  store (ADR-008, confirmed) — chosen over React Context for its granular per-field
  subscription model: a component reading only `hoveredNodeId` doesn't re-render on every
  `searchQuery` keystroke, which matters once dozens of nodes each read from the store every
  frame. Node *positions* are not store state at all — they're derived, pure data from
  `universe/layout.ts`/`universe/mapping.ts`, recomputed via `useMemo` from already-fetched
  API responses, never stored redundantly.

### AI Mode Abstraction

- ✅ CONFIRMED (Phase 05) — A provider-style interface (`app/ai/provider.py`'s `AIProvider`
  ABC) with two implementations selected by `APP_AI_PROVIDER` (`offline` / `anthropic` /
  `disabled`), no silent fallback between them:
  1. **Offline deterministic explainer** (default, no API key, no network call) — produces
     template-based natural-language summaries strictly from the computed payload's own
     fields. This satisfies principle 4 outright, and gives principle 3 a structurally
     enforced ceiling: the template can only reference fields that exist in the computed
     payload, so it cannot invent a number.
  2. **Real LLM provider** — ✅ CONFIRMED as Anthropic's Messages API, called directly via
     `httpx` (already a project dependency) rather than an SDK — see ADR-014. Opt-in only,
     user-supplied API key via environment variable, never committed.
- ✅ CONFIRMED — every AI call receives only the already-computed, size-bounded evidence
  dict as context and an instruction to explain, never raw dataset rows plus "compute a new
  number." This mirrors the ZIP's own `PHASE_05_AI_ANALYTICS` prompt: "The LLM is an
  interpreter, not the source of truth."

### Infrastructure

| Technology | Decision | Status | Rationale |
|---|---|---|---|
| Docker (multi-stage, separate frontend/backend images) | Adopted | ✅ CONFIRMED | Reproducible local/prod parity; finalized in Phase 08, an optional minimal skeleton may start in Phase 01. |
| docker-compose | Adopted | ✅ CONFIRMED | One-command local run for frontend + backend (+ future services). |
| Health checks | Adopted | ✅ CONFIRMED | `/health` on the backend, wired into compose; introduced as early as Phase 01. |

## System Overview (textual)

```
                         ┌───────────────────────────────┐
                         │        Browser (Client)        │
                         │  React + R3F Universe UI        │
                         │  ┌───────────┐  ┌────────────┐ │
                         │  │ 3D Scene  │  │ Inspector  │ │
                         │  │ (nodes,   │  │ Panels     │ │
                         │  │ links)    │  │ (computed  │ │
                         │  └───────────┘  │ vs AI)     │ │
                         │                 └────────────┘ │
                         └───────────────┬─────────────────┘
                                         │ REST/JSON (/api/v1)
                         ┌───────────────▼─────────────────┐
                         │           FastAPI Backend         │
                         │ ┌─────────┐ ┌─────────┐ ┌───────┐│
                         │ │Ingestion│ │Profiling│ │Analytics││
                         │ └─────────┘ └─────────┘ └───────┘│
                         │ ┌─────────┐ ┌──────────────────┐ │
                         │ │   ML    │ │  AI Mode          │ │
                         │ │(sklearn)│ │  (offline default │ │
                         │ └─────────┘ │  / real, opt-in) ─┼─┼──▶ external LLM API
                         │             └──────────────────┘ │   (only if user enables)
                         └───────────────┬───────────────────┘
                                         │ filesystem
                         ┌───────────────▼─────────────────┐
                         │  data/uploads/ (gitignored)       │
                         │  raw files + metadata sidecars    │
                         └───────────────────────────────────┘
```

Egress to an external network only occurs from the AI module, and only when the user has
explicitly configured a real provider (principle 4).

## Module Boundaries

**Frontend** (`frontend/src/`, created Phase 01):
- `universe/` — the mapping layer (`mapping.ts`, `layout.ts`), R3F scene components,
  camera, connection lines, performance-tier detection, and the 2D fallback (Phase 07) —
  see "Universe Architecture" below
- `panels/` — inspector panel UI, computed/AI-generated visual distinction (Phase 06/07) —
  see "Frontend Integration Architecture" and "Universe Architecture" below
- `viz/` — 2D chart components, hand-rolled SVG (Phase 06; see ADR-015)
- `api-client/` — the *only* module allowed to call the backend (Phase 01/06)
- `state/` — per-dataset session context (Phase 06); Zustand for 3D scene *interaction*
  state (Phase 07, see "3D Interaction & State" above)
- `features/` — one directory per UX-flow step (upload, workspace, quality, analytics, ml,
  ai, universe) (Phase 06/07)
- `components/` — reusable, feature-agnostic UI primitives (Phase 06)
- `hooks/` — data-fetching hooks (`useAsync`/`useLazyAsync`) (Phase 06)

**Backend** (`backend/`, created Phase 01):
- `ingestion/` — upload, validation, storage (Phase 02)
- `profiling/` — data quality engine + statistics (Phase 03) — see "Profiling
  Architecture" below for its internal module breakdown
- `ml/` — baseline model training/evaluation (Phase 04)
- `ai/` — mode abstraction + implementations (Phase 05) — see "AI Analytics Architecture"
  below for its internal module breakdown
- `api/` — thin FastAPI routers only; no business logic lives here

No module reaches into another module's internals — only through its public interface
(`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md`). `profiling/` reuses `ingestion/`'s
`StorageService` through one small, deliberate addition to its existing public interface
(`get_raw_file_path`) rather than building a second, incompatible dataset storage system.

## Profiling Architecture (Phase 03)

`app/profiling/` is split by responsibility, each piece independently unit-tested:

- `errors.py` — `ProfilingError` (same `{code, message, status_code}` shape as
  `ingestion.errors.IngestionError`, kept as an independent class per the module-isolation
  rule above).
- `schemas.py` — every Pydantic response model (`DatasetProfile`, `ColumnProfile`,
  `QualitySummary`, `CorrelationResult`, `DistributionResult`, …). All fields are computed
  facts; nothing here is or ever contains AI-generated text (that's Phase 05's job, wrapping
  these payloads, never extending them).
- `loader.py` — loads a dataset's `DataFrame` via `ingestion.StorageService`, re-reading
  from disk on every call (no caching layer — a deliberate simplicity choice for a
  local-first v1 with no dataset-size ceiling problem yet; revisit if profiling becomes a
  hot path).
- `column_types.py` — conservative, deterministic semantic-type classification
  (numeric/boolean/datetime/categorical/text/unknown) layered on top of the raw pandas
  dtype, never replacing it.
- `numeric_stats.py` / `categorical_stats.py` / `datetime_stats.py` — per-type descriptive
  statistics.
- `column_profile.py` / `dataset_profile.py` — orchestration: per-column and whole-dataset
  aggregation.
- `quality.py` — deterministic data-quality findings (see below).
- `correlation.py` — Pearson correlation between numeric column pairs.
- `distribution.py` — histogram/binning data for numeric columns.

**Numeric edge-case policy:** infinite values are excluded from descriptive statistics
(min/max/mean/median/std/quartiles) — computed only over the finite subset — and reported
separately as `infinite_count`, because `inf`/`-inf`/`NaN` are not valid JSON number
tokens and letting one infinite value silently turn every statistic into `inf` would
misrepresent an otherwise well-behaved column. Zero/negative counts are computed over all
non-null values, since a `0` or `-inf` is still meaningfully zero/negative.

**Quality check thresholds** (fixed, documented constants — not learned or guessed; see
`decisions/DECISIONS_LOG.md` ADR-011): missing-value severity at 20%/50% (warning/
critical), near-constant at ≥95% single-value share, high-cardinality categorical at >50%
unique ratio, mixed-type detection at 10–90% numeric-coercible ratio, datetime detection at
≥90% parse success.

**Correlation strategy:** Pearson only; missing values handled *pairwise* per column pair
(not one dataset-wide `dropna`, which would discard usable pairs unnecessarily); a
configurable `minimum_observations` (default 3) below which a pair is skipped, not
fabricated; an explicit `"insufficient_data"` status (with a human-readable `message`) when
fewer than 2 numeric columns exist or every pair lacks enough overlapping data — never a
failure, never a silently empty-looking success.

**Distribution strategy:** `numpy.histogram` over each numeric column's finite values, with
a fixed default of 10 bins; a column with no finite values or where every finite value is
identical is reported in `skipped_columns` rather than emitting a degenerate or fabricated
histogram; non-numeric and boolean columns are always skipped.

**Edge cases handled explicitly, not silently:** a header-only (0-row) dataset profiles
cleanly with an `empty_dataset` quality finding, not an error; a dataset with zero columns
returns a `zero_columns` critical finding without attempting further checks; a dataset
metadata record whose raw file has been removed or corrupted out-of-band raises a
structured `dataset_unreadable`/`dataset_not_found` error, never a bare 500.

## Machine Learning Architecture (Phase 04)

`app/ml/` is split by responsibility, mirroring `app/profiling/`'s pattern:

- `errors.py` — `MLError` (same `{code, message, status_code}` shape as
  `IngestionError`/`ProfilingError`, independent class).
- `schemas.py` — every Pydantic request/response model. Every result explicitly separates
  observed dataset facts, task type, selected features, preprocessing, model, metrics,
  warnings, and limitations (this phase's Core Principle) — nothing here is or ever
  contains AI-generated text.
- `task_detection.py` / `task_info.py` — deterministic task-type suitability evaluation
  (reusing Phase 03's `detect_semantic_type`) and static task-type metadata.
- `target_validation.py` — every target-column validation rule (existence, missingness,
  cardinality, class-imbalance warnings), each with a specific error `code`.
- `preprocessing.py` — feature selection (excluding target-duplicates, constant columns,
  and unsupported semantic types) and `ColumnTransformer` construction.
- `splitting.py` — deterministic, stratified-where-appropriate train/test splitting.
- `models.py` — the fixed baseline model registry (see ADR-013 for what's included and
  why XGBoost isn't, ADR-004).
- `evaluation.py` — classification/regression metrics, with an explicit
  `unavailable_metrics` map for anything mathematically invalid to compute (multiclass
  ROC-AUC, R² on a single-sample test set, etc.).
- `training.py` — orchestration: validates, selects features, splits once, then fits and
  evaluates a single model's `Pipeline`.
- `comparison.py` — runs multiple models over the identical prepared split from
  `training.py`, returning one full result per model with no aggregate score or declared
  winner.

**Leakage prevention is structural**, not a checklist: the split happens before any
preprocessing exists; each model's `Pipeline` (preprocessing + estimator) is fit only on
the training split, and prediction on the test split reuses already-fitted parameters
(standard scikit-learn `Pipeline` semantics, not a custom mechanism). A candidate feature
that is byte-identical to the target column is detected and excluded
(`duplicate_of_target`) as an explicit anti-leakage check beyond what `Pipeline` alone
would catch.

**"Train" and "evaluate" are one atomic operation** (`POST .../ml/train`) rather than two
separate stateful steps — there is no model-persistence/serving layer in this project (out
of scope per the phase prompt), so there is nothing to evaluate later that training itself
doesn't already produce. See ADR-013.

**Model set is fixed and small** by design (`PHASE_04_ML_ENGINE/PHASE_PROMPT.md`: "Do not
add a huge model zoo"): `LogisticRegression`/`RandomForestClassifier` for classification,
`LinearRegression`/`Ridge`/`RandomForestRegressor` for regression. XGBoost was concretely
benchmarked and not adopted — see ADR-004 for the real numbers.

## AI Analytics Architecture (Phase 05)

`app/ai/` is split by responsibility, mirroring `app/profiling/`'s and `app/ml/`'s pattern:

- `errors.py` — `AIError` (same `{code, message, status_code}` shape as
  `IngestionError`/`ProfilingError`/`MLError`, independent class).
- `schemas.py` — every Pydantic request/response model, including `AIAnalyzeResponse`/
  `AIQueryResponse`'s `computed` + `ai_explanation` envelope (see "Data Flow" below).
- `provider.py` — the `AIProvider` ABC (`is_available()`, `generate()`) every provider
  implements, so `service.py` never depends on a specific vendor.
- `providers/offline.py` — the default, always-available provider; pure string
  interpolation into fixed templates, described further under "The Grounding Guarantee"
  below.
- `providers/anthropic_provider.py` — the real-LLM provider (ADR-014); every failure mode
  (missing key, timeout, network error, 401/429/5xx, malformed response) is caught and
  re-raised as a structured `AIError`, never a raw `httpx` exception.
- `factory.py` — `get_provider(settings)`: `disabled` → `None`, `anthropic` → an
  `AnthropicProvider` (even if misconfigured — its own `is_available()` reports that
  honestly; the factory never silently substitutes the offline provider), otherwise →
  `OfflineProvider`.
- `security.py` — `SYSTEM_INSTRUCTIONS` (the untrusted-data hierarchy) and
  `build_user_prompt()`, which structurally separates evidence-as-data from the request.
- `evidence.py` — deterministic, size-bounded evidence builders, one per capability, each
  reusing Phase 02-04's own already-computed output (`build_dataset_profile`,
  `build_quality_summary`, `profile_column`, `compute_correlation` — never re-deriving a
  statistic independently, which would risk it drifting from what Phase 03/04 actually
  computed).
- `routing.py` — deterministic-first question routing (`route_question`): a fixed set of
  recognized question shapes (duplicates, missing values, correlation, column statistics,
  ML metrics) resolved by direct lookup into Phase 02-04 output, never by asking a
  provider to compute a number.
- `service.py` — orchestration: builds evidence, calls the configured provider, assembles
  the response contract. Never raises for a provider failure (turns it into
  `available: false` + `reason`); only raises `AIError` for a genuinely bad request (unknown
  column, malformed `ml_result`).

### The Grounding Guarantee

The core architectural invariant (`01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section
22): **the `computed` field is built from deterministic evidence and frozen *before* any AI
provider is ever called, and is never written to afterward.** A provider's `generate()`
returns only `ProviderResult.text` — there is no parameter, return path, or shared mutable
state through which a provider could alter `computed`. This is enforced structurally, not
just by prompting, and proven by `tests/test_ai_grounding.py`: a `FakeProvider` configured
to return a deliberately fabricated/wrong answer (e.g. "this dataset actually has 999
rows") never changes `response.computed["row_count"]`, `["numeric_stats"]["mean"]`,
correlation coefficients, ML metrics, or a deterministic query's `resolved_answer` — only
`ai_explanation.text` reflects the fabrication.

The offline provider is additionally *structurally* immune to prompt injection: it never
"interprets" a string, it only ever substitutes named evidence fields into fixed template
sentences (`providers/offline.py`), so a malicious column name or cell value can appear
verbatim in the rendered text but can never change *which* text is rendered or what data it
reports. The real (Anthropic) provider relies on the same evidence-as-untrusted-data
structure plus explicit system instructions (`security.py`) — see `test_ai_security.py`
for injection-attempt tests via both column names and cell values.

### Deterministic-First Question Routing

Free-form questions to `POST .../ai/query` are matched against a small, fixed set of
patterns (`routing.py`) *before* any provider is involved — e.g. "how many rows are
duplicated" resolves directly from `build_dataset_profile`'s own duplicate count, never
from an LLM's arithmetic. Column-statistic questions ("what is the average of X") use
word-boundary regex matching against real column names (`\bcolumn_name\b`), not a naive
substring check — a naive check would let "age" falsely match inside "average" and answer
with the wrong column's statistic, which would violate the grounding principle by
"resolving" a question that was never actually about that column. Unmatched questions fall
through to `EXPLANATION` (dataset-quality-shaped, given full bounded context) or
`ANALYTICAL_INTERPRETATION` (open-ended, still evidence-only) — never silently guessed.

### Data Minimization & Secret Protection

- Evidence sent to any provider is capped: `MAX_SUMMARY_COLUMNS=30`,
  `MAX_QUALITY_FINDINGS=20`, `MAX_CORRELATION_PAIRS=10` (sorted by `abs(coefficient)`, so
  the most significant pairs survive the cap), plus the ≤5 sample values already capped by
  Phase 03's column profiling. Raw dataset rows are never sent — only these bounded,
  already-aggregated facts.
- The Anthropic API key is read once from `Settings` (a Pydantic `SecretStr`, never logged)
  and used only in the `x-api-key` HTTP header — no response schema has a field that could
  hold it, and no evidence dict ever contains application configuration.

## Frontend Integration Architecture (Phase 06)

The 2D application wired up in this phase — the "List/Table" fallback view
`UI_UX_SPEC.md` §3 requires Phase 06 to build first, ahead of Phase 07's 3D layer on top:

- **`api-client/`** — `http.ts` holds the single `fetch` wrapper (`request()`) and
  `ApiError` (carrying `status` and, when the backend returned its own structured
  `{"error": {"code", "message"}}` envelope, `code`); every other file in this directory is
  a thin, typed function per backend endpoint, grouped by domain (`datasets.ts`,
  `profiling.ts`, `ml.ts`, `ai.ts`), re-exported through `index.ts`. `types.ts` mirrors the
  backend's actual Pydantic schemas field-for-field — verified against the schema source
  files, never invented (see ADR-015 for why this stays hand-written rather than
  OpenAPI-codegen'd). No component ever calls `fetch` directly.
- **`hooks/useAsync.ts`** — `useAsync(fn, deps)` runs on mount/dependency-change (view data
  loads); `useLazyAsync(fn)` runs only when explicitly triggered (user actions: upload,
  train, ask a question). Both track the same `{idle | loading | success | error}` state
  shape, which is what every view's loading/error/empty rendering is driven from
  (`UI_UX_SPEC.md` §8).
- **`features/`** — one directory per UX-flow step (`upload/`, `workspace/`, `quality/`,
  `analytics/`, `ml/`, `ai/`), each a thin page component composing `api-client` calls
  (via the hooks above) with `components/`/`viz/`/`panels/` primitives. No business
  calculation happens here — every displayed value is passed through from the API
  response, never recomputed client-side (this phase's own acceptance criterion).
- **Routing (`react-router-dom`, ADR-015)** — `/` (upload + existing-dataset list),
  `/datasets/:datasetId` (workspace layout: fetches `DatasetMetadata` once, provides it to
  nested routes via `useOutletContext`) with nested routes `/quality`, `/analytics`, `/ml`,
  `/ai`. An unknown route redirects to `/` rather than rendering a broken page.
  `state/DatasetSessionContext.tsx` is provided at the workspace layout level, scoped to
  one dataset session — the last trained `ModelResult` (needed by the AI `ml_explanation`
  capability, since the backend has no model-persistence layer, ADR-013) lives here, not
  in a global store.
- **`panels/AIExplanationBlock.tsx` / `EvidenceSources.tsx`** — the concrete implementation
  of `UI_UX_SPEC.md` §4.6's computed-vs-AI-generated visual contract: a subordinate,
  tinted block below the computed data it explains, labeled "AI explanation — `<provider>`
  `(<model>)`", rendering `ai_explanation.text` as plain text only (never
  `dangerouslySetInnerHTML` — AI output is untrusted content, per this phase's own
  security requirement) alongside the response's real `limitations` and
  `evidence_sources`. `AIUnavailableNotice` renders instead whenever `available` is
  `false`, using the backend's own `reason` — the deterministic `computed` data is always
  rendered regardless of AI availability, since the grounding contract (Phase 05) means it
  was never dependent on a provider succeeding.
- **`viz/`** — hand-rolled SVG components (`Histogram`, `CorrelationBar`, `FrequencyList`),
  each rendering the backend's own already-computed bins/coefficients/frequencies verbatim
  — no client-side binning or statistical recomputation. See ADR-015 for why no charting
  library was added.

## Universe Architecture (Phase 07)

The 3D "Data Intelligence Universe" is a presentation layer added on top of Phase 06's
already-complete, already-tested 2D application — it introduces no new backend endpoint,
no new computation, and no change to any existing route's behavior. `frontend/src/universe/`
is split by responsibility, mirroring the backend's own `profiling/`/`ml/`/`ai/` pattern:

- **`types.ts`** — the scene-agnostic domain model (`UniverseNode`/`UniverseEdge`/
  `NodeVisualState`) the mapping layer produces and every renderer consumes. Plain data,
  no Three.js/R3F import — `ARCHITECTURE.md`'s "the 3D scene should receive clean domain
  objects" rule, enforced by file boundary.
- **`mapping.ts`** — `buildUniverseGraph()`: a pure, synchronous function turning already-
  fetched `DatasetMetadata`/`DatasetProfile`/`QualitySummary`/`CorrelationResult`/
  `ModelResult`/`AIStatusResponse` into a `UniverseGraph`. No `fetch` call lives here or
  anywhere under `universe/` — `features/universe/UniversePage.tsx` is the only place that
  calls the API client, via the same `useAsync`/`useLazyAsync` hooks every other page uses.
  Every node/edge field traces to a real response field; nothing is invented (see §4.1/ADR-
  016 for the exact node taxonomy and visual-encoding rules this function implements).
- **`layout.ts`** — deterministic spatial placement (FNV-1a hash + a mulberry32 PRNG step
  seed a per-dataset rotation offset for the golden-angle feature-ring spiral; domain-node
  positions are a fixed function of a constant ordering, no seed needed). Same input always
  produces the same positions — no `Math.random()` anywhere in this file.
- **`tiers.ts`** — `detectPerformanceTier()` and `usePrefersReducedMotion()`: the concrete,
  testable logic behind §4.7/§6/§9's performance-tier and reduced-motion resolutions.
- **`visualState.ts`** — `resolveNodeVisualState()`: combines a node's structural baseline
  (`available`/`error`, from the mapping layer) with interaction-time state (hover/
  selection/loading, from the store) into the single state every node renders, per a fixed
  precedence (§4.2). Kept separate from `mapping.ts` so the mapping layer stays interaction-
  free and this precedence logic is independently unit-testable without React or WebGL.
- **`filtering.ts`** — `filterFeatureNodes()`/`hasActiveFilters()`: pure search/filter logic
  shared by the 3D scene, the 2D fallback, and `features/universe/Search.tsx`/`Filters.tsx`,
  so all three narrow the identical feature set consistently.
- **`sceneTokens.ts`** — the single source of truth for 3D material colors, mirroring
  `tailwind.config.js`'s 2D tokens (Three.js materials need real hex values, not Tailwind
  classes) — the concrete implementation of "every visual encoding must be documented and
  consistent" (§26).
- **`UniverseScene.tsx`** / **`DatasetCoreNode.tsx`** / **`DomainNode.tsx`** /
  **`FeatureNode.tsx`** / **`CorrelationEdge.tsx`** / **`SceneLine.tsx`** /
  **`NodeLabel.tsx`** / **`useFloat.ts`** — the R3F scene itself: `Canvas` + lighting +
  `CameraControls` + node/edge meshes, each a thin renderer over the domain model above.
  Click/hover handlers only ever call `state/universeStore.ts` actions — no business logic
  lives in a scene component.
- **`UniverseErrorBoundary.tsx`** — a class-component error boundary scoped to the Universe
  page only: a render error anywhere inside the Canvas swaps in the 2D fallback with an
  explanatory message, without affecting any other tab (`errorHandling` requirement, phase
  brief §38).
- **`UniverseFallback.tsx`** — the 2D list/table view built from the identical
  `UniverseGraph`: a dataset summary, a domain grid (linking into the real Quality/
  Analytics/ML/AI tabs), a searchable/filterable feature table, and a correlation list —
  full data parity with the 3D scene, only the spatial metaphor is dropped (§3/§4.7).
- **`features/universe/UniversePage.tsx`** — orchestration: fetches profile/quality/
  correlation via `useAsync` (the same contract as every other page), reads the session's
  `lastMlResult` (`state/DatasetSessionContext.tsx`, unchanged from Phase 06) and AI status,
  builds the graph via `useMemo`, resolves the performance tier and the Scene-vs-Fallback
  branch, and hosts `UniverseHUD.tsx` (Search/Filters/Legend/Reset View/2D-3D toggle) and
  `panels/DetailPanel.tsx` (the shared slide-in shell, Framer Motion — already a project
  dependency, no new one added).
- **`panels/{DatasetPanel,FeaturePanel,QualityPanel,CorrelationPanel,MLPanel,
  AIInsightPanel}.tsx`** — the six inspector panels (§15/§16), each thin: they receive
  already-fetched data as props (no duplicated fetch/compute logic against the same
  endpoints `UniversePage` already called) and reuse `components/{Card,Badge,StatValue}.tsx`
  plus `panels/{AIExplanationBlock,EvidenceSources}.tsx` verbatim, preserving the computed-
  vs-AI-generated visual contract Phase 06 already built. `AIInsightPanel.tsx` is the one
  exception with its own AI call (`analyzeDatasetSummary`) — a single representative
  capability offered inline, with a link to the full 5-capability + Q&A `/ai` tab rather
  than duplicating it.

**Code-splitting:** `App.tsx` lazy-loads `UniversePage` (`React.lazy` + `Suspense`) — three.js/
`@react-three/fiber`/`@react-three/drei` are a genuinely large dependency (confirmed by
`vite build`'s own chunk-size warning: ~1.05 MB before splitting) that only the Universe tab
needs. After splitting, the main bundle is ~215 KB and the Universe chunk (~1.05 MB, loaded
only on demand) is separate — a real, measured performance improvement, not a guess.

**Only new runtime dependency: `zustand`** (ADR-008, resolved). No `@react-three/
postprocessing`, no new charting/animation library — see §4.7 above for why post-processing
was deliberately not added, and ADR-016 for the full dependency-discipline reasoning.

## Data Flow & the Computed/AI-Generated Contract

Flow: `upload → validate → store → profile → statistics → (optional) ML → (optional) AI
explanation → Universe render`.

✅ CONFIRMED contract: any API response field that can contain AI-generated text is wrapped
in an explicit envelope, e.g.:

```json
{
  "computed": { "row_count": 10432, "null_percentage": 3.2 },
  "ai_explanation": {
    "source": "ai_generated",
    "provider": "offline",
    "text": "This dataset has 10,432 rows with 3.2% missing values.",
    "generated_at": "2026-09-17T10:00:00Z"
  }
}
```

`computed` is never absent when `ai_explanation` is present, and the frontend must render
them with visually distinct treatment (`UI_UX_SPEC.md`). This is the concrete, enforceable
form of product principles 2 and 3.

## API Contract Philosophy

- REST over JSON, versioned under `/api/v1`. ✅ CONFIRMED.
- Pydantic models are the single source of truth; FastAPI's auto-generated OpenAPI schema
  is the contract the frontend's typed API client is generated/validated against
  (Phase 01/06). ✅ CONFIRMED.
- Errors use a consistent, structured error schema (🟡 ASSUMED shape, finalized Phase 02) —
  never a bare 500 with no explanation.

## Security & Privacy

- Local-first by default: no dataset content leaves the machine unless the user explicitly
  configures a real AI provider (principle 4). ✅ CONFIRMED.
- No secrets, API keys, or `.env` files are ever committed — only `.env.example` with
  placeholder values.
- Upload validation must guard against path traversal, oversized files, and MIME/type
  spoofing — concrete checks specified and tested in Phase 02, hardened further in Phase 08.

## Performance & Scalability Notes

- ✅ CONFIRMED (Phase 02) — dataset size ceiling for v1 is the 50 MB per-file upload limit
  (see "Data Storage" above); no separate row/column ceiling is enforced. "Comfortably fits
  in memory on a single developer machine" (no streaming/chunked processing in v1) remains
  the operating assumption behind that number, not a separate open question anymore.
- The 3D Universe must maintain usability on lower-end hardware via explicit performance
  tiers and a 2D fallback — a hard requirement, detailed in `UI_UX_SPEC.md`.

## Deployment Topology

- **Dev:** `vite` dev server (frontend) + `uvicorn --reload` (backend), run directly on the
  host — no Docker required for day-to-day development.
- **Prod-like/local release:** `docker compose up` runs both services together with health
  checks (Phase 08).
- Public cloud hosting is explicitly out of scope for v1 — the Docker setup is
  deployment-ready but no specific host is chosen.

## Decision Log

Full architecture decision records live in
[`decisions/DECISIONS_LOG.md`](decisions/DECISIONS_LOG.md). Every dependency or
architecturally significant choice made during implementation gets an entry there before or
alongside its use.

## Open Questions / Risks

- **Risk:** visx's lower-level API may slow down Phase 03 delivery relative to a
  higher-level chart library; mitigated by the documented fallback and by acceptance
  criteria not being tied to a specific library, only to correctness and visual quality.
- **Risk (resolved, Phase 07):** the "premium, not decorative" 3D bar (principle 6) was
  inherently more subjective than a functional requirement; mitigated by the concrete node/
  state/anti-goal checklist in `UI_UX_SPEC.md` §1/§4, run as a recorded manual QA pass — see
  `01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_REPORT.md` for the actual checklist result.
- **Risk (accepted, Phase 07):** correlation edges are not individually clickable inside the
  3D scene (thin-line raycasting at a distance is unreliable); mitigated by
  `panels/CorrelationPanel.tsx` giving the identical pairs/coefficients in 2D from the
  Analytics domain node — an explicit "3D for spatial context, 2D for precision" trade-off,
  not an oversight.

---
*Related: [PRODUCT_SPEC.md](PRODUCT_SPEC.md) · [UI_UX_SPEC.md](UI_UX_SPEC.md) ·
[decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md) ·
[../00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md](../00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md)*
