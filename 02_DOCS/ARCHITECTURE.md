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
| React Three Fiber + Three.js | Adopted | ✅ CONFIRMED | The Universe is not optional — it's the product's primary interface. R3F is the standard, well-maintained React binding, keeping the 3D scene declarative and testable at the state level. `@react-three/drei` is the standard helper library (camera controls, text, instancing) — 🟡 ASSUMED, confirmed in Phase 07. |
| Data visualization library | **visx** (Airbnb), with D3 utilities underneath | 🟡 ASSUMED | Evaluated against Recharts, Nivo, and Observable Plot. Higher-level libraries (Recharts/Nivo) were set aside because their default visual identity reads as "generic dashboard" (principle 5) and their theming ceiling is lower than the "premium" bar `UI_UX_SPEC.md` sets. visx gives low-level control at the cost of more implementation work. **Revisit in Phase 03** when real chart requirements are known; Observable Plot is the documented fallback if implementation velocity suffers. |

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

- ✅ CONFIRMED — 3D scene state (node positions, selection, hover, focus/camera target) is
  managed in a dedicated frontend state slice. Library choice 🟡 ASSUMED as **Zustand**
  (lightweight, avoids re-render storms in a frequently-updating 3D scene) — confirmed in
  Phase 07.

### AI Mode Abstraction

- ✅ CONFIRMED — A provider-style interface with at minimum two implementations:
  1. **Offline deterministic explainer** (default, no API key, no network call) — produces
     template-based natural-language summaries strictly from the computed payload's own
     fields. This satisfies principle 4 outright, and gives principle 3 a structurally
     enforced ceiling: the template can only reference fields that exist in the computed
     payload, so it cannot invent a number.
  2. **Real LLM provider** (opt-in, user-supplied API key via environment variable, never
     committed) — 🟡 ASSUMED to be an Anthropic Claude model as the first real integration,
     not a hard architectural commitment; the interface is provider-agnostic. Confirmed in
     Phase 05.
- ✅ CONFIRMED — every AI call receives only the already-computed JSON payload as context
  and an instruction to explain, never raw data plus "compute a new number." This mirrors
  the ZIP's own `PHASE_05_AI_ANALYTICS` prompt: "The LLM is an interpreter, not the source
  of truth."

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
- `universe/` — R3F scene, node components, camera, connection lines (Phase 07)
- `panels/` — inspector panel UI, computed/AI-generated visual distinction (Phase 06/07)
- `viz/` — 2D chart components (visx-based) (Phase 03)
- `api-client/` — the *only* module allowed to call the backend (Phase 01/06)
- `state/` — Zustand stores (Phase 07)

**Backend** (`backend/`, created Phase 01):
- `ingestion/` — upload, validation, storage (Phase 02)
- `profiling/` — data quality engine + statistics (Phase 03) — see "Profiling
  Architecture" below for its internal module breakdown
- `ml/` — baseline model training/evaluation (Phase 04)
- `ai/` — mode abstraction + implementations (Phase 05)
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

- ❓ Final AI real-provider choice (Phase 05).
- **Risk:** visx's lower-level API may slow down Phase 03 delivery relative to a
  higher-level chart library; mitigated by the documented fallback and by acceptance
  criteria not being tied to a specific library, only to correctness and visual quality.
- **Risk:** the "premium, not decorative" 3D bar (principle 6) is inherently more
  subjective than a functional requirement; mitigated by the concrete node/state/anti-goal
  checklist in `UI_UX_SPEC.md`, used as literal acceptance criteria in Phase 07.

---
*Related: [PRODUCT_SPEC.md](PRODUCT_SPEC.md) · [UI_UX_SPEC.md](UI_UX_SPEC.md) ·
[decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md) ·
[../00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md](../00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md)*
