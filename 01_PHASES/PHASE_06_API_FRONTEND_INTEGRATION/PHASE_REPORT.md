# Phase Report

## Phase
PHASE 06 — API + Frontend Integration

## Date
2026-09-18

## Branch
`phase/06-api-frontend-integration` (branched from `origin/main` at `32370b8`, the
human-merged, Phase-05-included baseline)

## What was built

- **`frontend/src/api-client/`** — extended from the Phase 01 health-check-only client:
  - `http.ts` — the single `fetch` wrapper (`request()`) and `ApiError`, normalizing both
    of the backend's error shapes (`{"error": {"code","message"}}` and FastAPI/Pydantic's
    `{"detail": [...]}`) into one consistent error every caller handles the same way.
  - `types.ts` — every backend response/request model, transcribed field-for-field from
    the real Pydantic schema files (`backend/app/{ingestion,profiling,ml,ai}/schemas.py`),
    including capability-specific "evidence" interfaces for the AI layer's intentionally
    open `computed` dict.
  - `datasets.ts` / `profiling.ts` / `ml.ts` / `ai.ts` — one typed function per backend
    endpoint, re-exported through `index.ts`.
- **`frontend/src/hooks/useAsync.ts`** — `useAsync` (mount-time data loads) and
  `useLazyAsync` (user-triggered actions), the shared `{idle|loading|success|error}` state
  shape every view's loading/error rendering is built on.
- **`frontend/src/components/`** — `Card`, `Badge`, `StatValue` (monospace numeric
  treatment per `UI_UX_SPEC.md` §2), `Tabs`, `LoadingSkeleton`/`ErrorState`/`EmptyState`.
- **`frontend/src/panels/`** — `AIExplanationBlock.tsx`/`AIUnavailableNotice`/
  `EvidenceSources.tsx`, the concrete implementation of the computed-vs-AI-generated
  visual contract (`UI_UX_SPEC.md` §4.6): a subordinate, tinted, plain-text-only block
  (never `dangerouslySetInnerHTML` — AI output is untrusted content) below the computed
  data it explains.
- **`frontend/src/viz/`** — `Histogram`, `CorrelationBar`, `FrequencyList`: hand-rolled SVG
  components rendering the backend's own already-computed bins/coefficients verbatim, no
  charting dependency (see ADR-015).
- **`frontend/src/state/`** — `DatasetSessionContext`/`useDatasetSession`, one small React
  Context per dataset workspace holding the last trained `ModelResult` (needed by the AI
  `ml_explanation` capability, since the backend has no model-persistence layer, ADR-013).
- **`frontend/src/features/`** — one page (or small set of pages) per UX-flow step:
  `upload/UploadPage.tsx` (dropzone + file input, client-side extension validation,
  loading/error states, existing-dataset list), `workspace/` (`WorkspaceLayout` + tab nav
  + `OverviewPage`), `quality/QualityPage.tsx`, `analytics/AnalyticsPage.tsx`
  (distributions + correlation), `ml/MlPage.tsx` (target selection → suitability →
  task/model → train → results), `ai/AiPage.tsx` + `QaPanel.tsx` (status, all 5
  capabilities, grounded Q&A with example questions).
- **Routing (`react-router-dom`, new dependency, ADR-015)** — `/` (upload/dashboard),
  `/datasets/:datasetId` (workspace layout, fetches `DatasetMetadata` once) with nested
  `/quality`, `/analytics`, `/ml`, `/ai` routes; unknown routes redirect to `/`.
- **`App.tsx`/`main.tsx`** — replaced the Phase 01 placeholder shell (health-check badge +
  spinning R3F wireframe) with the real routed application; `BrowserRouter` added at the
  root.
- **33 new frontend tests** across 12 files (4 `api-client` contract tests, 8 feature-page/
  panel tests), using Vitest + React Testing Library + the newly added
  `@testing-library/user-event` (dev dependency).

## Architecture decisions

- **ADR-015 (new)**: records the routing choice (`react-router-dom`, declarative API
  only), the hand-rolled-SVG charting decision (supersedes the Phase 00 visx assumption —
  Phase 03 never actually exercised it, so it was still open), the no-state-library
  decision (`useAsync`/`useLazyAsync` + one small Context, not TanStack Query/Zustand), and
  why the API client stays hand-written TypeScript rather than OpenAPI-codegen'd this
  phase.
- `02_DOCS/ARCHITECTURE.md` gained a "Frontend Integration Architecture (Phase 06)"
  section; its "Stack Evaluation" → "Frontend" table's visx row was updated from 🟡 ASSUMED
  to ✅ CONFIRMED (hand-rolled SVG, per ADR-015); "Module Boundaries" → "Frontend" was
  updated to list the new `features/`/`components/`/`hooks/` directories.
- `02_DOCS/UI_UX_SPEC.md` §3 and §7 updated from forward-looking assumptions to ✅
  CONFIRMED/BUILT, reflecting what actually exists now.
- `02_DOCS/API_CONTRACTS.md` created — the finalized, human-readable API contract
  reference this phase's own prompt required, verified against the real schema files and
  a live running server.

## Files/components added or changed

New: `frontend/src/api-client/{http,datasets,profiling,ml,ai,index}.ts` (+ their `.test.ts`
files), `frontend/src/hooks/useAsync.ts`, `frontend/src/components/{Card,Badge,severity,
StatusStates,StatValue,Tabs}.tsx`, `frontend/src/panels/{AIExplanationBlock,
EvidenceSources}.tsx`, `frontend/src/viz/{Histogram,CorrelationBar,FrequencyBar}.tsx`,
`frontend/src/state/{DatasetSessionContext,sessionContextValue,useDatasetSession}.ts(x)`,
`frontend/src/features/**` (+ their `.test.tsx` files), `02_DOCS/API_CONTRACTS.md`,
`01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_REPORT.md`.
Changed: `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/main.tsx`,
`frontend/src/api-client/{client,types}.ts` (extended, `getHealth` preserved for backward
compatibility), `frontend/package.json`/`package-lock.json` (+`react-router-dom`,
+`@testing-library/user-event`), `02_DOCS/ARCHITECTURE.md`, `02_DOCS/UI_UX_SPEC.md`,
`02_DOCS/PRODUCT_SPEC.md` (Success Criteria items 2/5 annotated), `02_DOCS/
TESTING_STRATEGY.md`, `02_DOCS/decisions/DECISIONS_LOG.md` (ADR-015 added),
`00_AGENT_CONTROL/PROJECT_STATE.md`.
Removed from the primary flow (file kept on disk, not deleted): `frontend/src/scene/
UniversePlaceholder.tsx` is no longer rendered by `App.tsx` — it was an explicitly
honest "R3F pipeline check" placeholder for Phase 01, now superseded by the real 2D
application; Phase 07 owns the actual Universe scene.
Verified unchanged: `backend/` — no backend contract was modified to make frontend
implementation easier (this phase's own "Backend Contract Discipline" requirement); the
full 342-test backend suite still passes.

## Tests/checks

- Command: `npx tsc --noEmit` → Result: **0 errors.**
- Command: `npx eslint . --max-warnings 0` → Result: **0 errors, 0 warnings.**
- Command: `npm run build` (`tsc --noEmit && vite build`) → Result: **succeeded** (71
  modules transformed, ~214 KB JS / ~68 KB gzipped).
- Command: `npm run test` (Vitest) → Result: **33 passed**, 0 failed, across 12 test files.
- Command: `.venv/Scripts/python.exe -m pytest -q` (backend) → Result: **342 passed**, 0
  failed — confirms zero backend regression from this phase's work.
- Command: `.venv/Scripts/python.exe -m ruff check .` (backend) → Result: **All checks
  passed.**
- Real end-to-end verification (not just automated tests): started the real backend
  (`uvicorn`, port 8000) and the real frontend dev server (`vite`, port 5173)
  simultaneously, then drove the actual UI through the built-in browser tool:
  - Uploaded a real CSV (10 rows, a duplicate row, a missing value, a datetime column) via
    a simulated drag-and-drop onto the dropzone → real `201` response → automatic
    navigation to the new dataset's workspace.
  - **Overview**: real row/column/size/duplicate counts and the real per-column profile
    table (semantic types, null/unique percentages, sample values) rendered — cross-checked
    against the actual uploaded CSV content.
  - **Quality**: real findings (`duplicate_rows`, `missing_values`) rendered with correct
    severity badges and messages.
  - **Analytics**: real numpy-histogram bins rendered as SVG bars for `age`/`income`; real
    Pearson correlation (age×income, coefficient 0.982) rendered as a correlation bar with
    the causation disclaimer; non-numeric/skipped columns correctly listed.
  - **ML**: selected `income` as target — correctly reported *not* suitable for any task
    (9 non-null values, `MIN_ROWS_FOR_TRAINING` requires 10) with the real per-task
    reason from the backend, no fabricated suitability. Selected `age` instead (0% null),
    task `regression`, model `linear_regression`, clicked Train → a real live
    `POST .../ml/train` call → real metrics rendered (MAE 3.247709, MSE 13.115895, RMSE
    3.621587, R² 0.941707), real warning ("Only 10 usable rows…") and limitations.
  - **AI Insights**: status showed `Available` / `provider: offline` with zero
    configuration. Ran the `ML result` capability (enabled only after training, reading
    the trained result from `DatasetSessionContext`) → the AI explanation echoed the
    *exact* metrics just trained, verbatim, with `Supported by: ML Result`. Asked "How
    many rows are duplicated?" via the Q&A panel → real deterministic-lookup answer ("1
    row(s) are exact duplicates (10.0% of 10 total rows)."), correctly labeled
    `deterministic lookup`, with real evidence sources.
  - **Error path**: navigated directly to `/datasets/does-not-exist` → the real
    `dataset_not_found` (404) error rendered cleanly with a "Try again" action, no crash.
  - **Responsive check**: resized to mobile width (375×812) mid-flow on the AI Insights
    page — cards stacked to a single column, the computed/AI-explanation visual
    distinction remained clear, no horizontal overflow.
  - **Console**: zero errors at any point across the entire flow (`read_console_messages`
    checked repeatedly).
  - Verification dataset removed from `backend/data/uploads/` afterward; both dev servers
    stopped.
- Confirmed "no business calculations duplicated in UI": every numeric value rendered
  anywhere in `frontend/src/features/`/`viz/`/`panels/` is read directly from an API
  response field — verified by inspection (no client-side aggregation/statistics code
  exists outside of pure display formatting like `toFixed`/byte-to-KB conversion).

## Known limitations

- Playwright end-to-end tests (🟡 ASSUMED in `TESTING_STRATEGY.md`) were **not** added
  this phase — the equivalent full-stack flow was verified manually through the built-in
  browser tool instead (see "Tests/checks" above), and Vitest/RTL cover the component
  layer. Automating that exact flow with Playwright remains a reasonable future addition,
  not a gap in what was actually verified.
- No delete-dataset UI exists, because no delete endpoint exists on the backend (Phase 02
  never built one) — datasets accumulate under `backend/data/uploads/` until manually
  removed; out of this phase's scope to add a new backend endpoint for.
- Toasts/modals were not built — nothing in this phase's actual flow needed them (errors
  render inline per view, per `UI_UX_SPEC.md` §8's inline error-state requirement); noted
  in `UI_UX_SPEC.md` §7 as legitimately unbuilt rather than silently missing.
- The `.claude/launch.json` local dev-server launch config (gitignored, not part of the
  repository) had a pre-existing bug on this Windows environment (an unquoted spaced path
  as `runtimeExecutable`) that prevented starting the frontend preview; fixed locally
  (switched to `npm.cmd run dev`) to perform this phase's runtime verification. Since the
  file is gitignored and machine-local, this fix is not part of the committed changeset
  and does not affect other environments.
- Full design-token finalization (exact color palette, typography, motion timing) remains
  explicitly out of scope per `UI_UX_SPEC.md` §9 — deferred to Phase 07, as originally
  planned; this phase used the existing Phase 01 dark-surface/accent tokens as-is.

## Git

Commits (on `phase/06-api-frontend-integration`): `feat(phase-06): integrate frontend
with Phase 02-05 backend`, followed by a small commit recording that hash back into this
report and `PROJECT_STATE.md` (unavoidable, same reason as prior phases).

Remote branch: `origin/phase/06-api-frontend-integration` — pushed and existence verified
(see completion message).

## Next phase

**PHASE 07 — 3D Universe UI**
(`01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md`). Not started. Requires explicit
human approval before beginning.
