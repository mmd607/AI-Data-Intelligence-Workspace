# Testing Strategy

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED

This document defines **how** testing is done across the project. Each phase's own
`01_PHASES/<phase>/PHASE_PROMPT.md` defines **what** must be tested in that specific
phase — that per-phase list is authoritative for that phase's `DEFINITION_OF_DONE.md` gate;
this document is the shared methodology and tooling behind it.

---

## 1. Testing Pyramid

1. **Unit tests** — fastest, most numerous. Pure functions: validation logic, statistics
   calculations, scoring formulas, AI-template rendering.
2. **Integration tests** — module boundaries: API routes exercised via FastAPI's
   `TestClient`, frontend components exercised against a mocked API client.
3. **End-to-end tests** — critical user flows through the real (or docker-composed) stack:
   upload → profile → statistics → ML → (optional) AI explanation.
4. **Visual/manual QA** — specifically for the 3D Universe, where pixel-perfect automated
   testing is not a good use of effort; checked against the concrete checklist in
   `UI_UX_SPEC.md` §1/§4, not vibes.

## 2. Backend Tooling

- ✅ CONFIRMED — `pytest` as the test runner, FastAPI's `TestClient`/`httpx` for API-level
  integration tests (matches the ZIP's own baseline: "Testing: pytest for backend").
- 🟡 ASSUMED coverage target: **≥80% line coverage** for core logic modules (`ingestion/`,
  `profiling/`, `ml/`, `ai/`); a lower bar is acceptable for thin router/glue code (`api/`)
  where the logic is exercised indirectly by integration tests. Exact numbers are finalized
  and measured for real in Phase 08. **Actual, measured:**
  - Phase 03 — `app/profiling/`: 99% line coverage; the one uncovered line is a
    provably-unreachable defensive guard in a private helper (its only caller already
    checks the same condition first) — left uncovered deliberately rather than adding a
    contrived test or stripping a harmless safety check.
  - Phase 04 — `app/ml/`: **100% line coverage** (`pytest --cov=app.ml
    --cov-report=term-missing`) — every line, including edge cases like a NaN-poisoned
    ROC-AUC input and a high-cardinality categorical warning, is exercised by a real,
    meaningful test, not an artificially inflated one.
  - Phase 05 — `app/ai/`: **100% line coverage** (`pytest --cov=app.ai
    --cov-report=term-missing`, 342 tests total across the whole backend suite). The single
    exception is one documented, provably-unreachable defensive `raise` in
    `service._build_analyze_evidence` (guarded by a Pydantic-validated enum where every
    current member is already handled), marked `# pragma: no cover` with an inline
    explanation rather than covered by a contrived test.
  The goal throughout is 100% coverage of the important logic paths, not meaningless
  coverage inflation — see each phase's own report for what was deliberately left
  uncovered and why.
- Fixture datasets (small, synthetic, engineered to have known properties — known null
  counts, known duplicates, known distributions) live under a test-fixtures directory
  (🟡 ASSUMED path: `backend/tests/fixtures/`), are checked into git (they contain no
  real/PII data by policy, §7), and are the basis for the ZIP's own Phase 02 requirement:
  "valid CSV, empty CSV, malformed CSV, missing values, duplicate rows, mixed types" test
  fixtures.

## 3. Frontend Tooling

- ✅ CONFIRMED — **Vitest** + **React Testing Library** (+ **@testing-library/user-event**,
  added Phase 06) for component/unit/integration tests, matching the ZIP's own baseline
  ("Vitest/Playwright or equivalent for frontend"). **Actual, measured (Phase 06):** 12
  test files, 33 tests, all passing — `api-client/*.test.ts` (mocked-`fetch` contract
  tests per domain module) and one test file per `features/` page (upload success/
  validation-failure/server-error/loading states; profile/quality/analytics rendering and
  empty/error states; the full ML configure→validate→train flow including a training
  error; the AI page's available/unavailable/evidence-display states; the Q&A panel's
  grounded-answer and unsupported-question states).
- 🟡 ASSUMED, **not adopted this phase** — Playwright end-to-end tests. Phase 06's actual
  full-stack verification (real backend + real frontend dev server, the complete upload →
  overview → quality → analytics → ML → AI flow, including live model training and a
  grounded Q&A exchange) was performed manually through the built-in browser tooling
  instead — see `01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_REPORT.md` "Tests/
  checks" for the exact run. Automating that flow with Playwright remains a reasonable
  future addition (its own dependency-policy entry when adopted), not a Phase 06 gap in
  actual verification coverage.
- ❓ OPEN QUESTION — visual regression tooling (e.g. Percy, Chromatic) for the 3D scene is a
  nice-to-have, not adopted by default; would need its own dependency justification in
  `ARCHITECTURE.md`/`decisions/DECISIONS_LOG.md` before adoption.

## 4. 3D-Specific Testing Approach

The 3D Universe (Phase 07) is tested primarily through:
- **Logic/state-transition tests** — node state machine (`UI_UX_SPEC.md` §4.2: idle → hover
  → selected → loading → error → disabled), performance-tier selection logic, and
  `prefers-reduced-motion` behavior are all pure/near-pure logic that can be unit-tested
  without rendering WebGL.
- **Manual QA checklist** — a literal pass through `UI_UX_SPEC.md` §1's anti-goals and §4's
  node/interaction requirements, performed and recorded (not just asserted) at Phase 07.
- Full pixel-level 3D rendering tests are explicitly **not** pursued — low value relative to
  cost.

## 5. Data-Correctness Testing

- Golden-fixture datasets with deliberately known statistical properties are the backbone
  of profiling/statistics/ML correctness testing (Phases 02–04).
- Computed statistics are cross-validated against direct `pandas`/`numpy` reference
  calculations in the test itself (the test independently recomputes the expected value,
  rather than hardcoding a number that could silently drift from correctness).
- ML reproducibility is tested via fixed random seeds, asserting metric stability within an
  explicit, documented tolerance across repeated runs (Phase 04, matching the ZIP's own
  "reproducible random seeds" requirement).
- **Pattern established in Phase 03** (recommended for Phase 04+): pure computation
  functions (e.g. `compute_numeric_stats`, `compute_correlation`) are unit-tested with
  `pandas.Series`/`DataFrame` objects constructed directly in the test — no file I/O,
  precise control over edge cases (nulls, infinities, single values, empty data). Fixture
  CSV files under `backend/tests/fixtures/` are reserved for API-level integration tests
  that need to exercise the real upload → storage → load round-trip. Keeping the two
  separate avoids both slow, fixture-heavy unit tests and imprecise, hard-to-construct
  edge cases in integration tests.

## 6. AI-Layer Testing

✅ CONFIRMED (Phase 05) — `backend/tests/test_ai_*.py`, organized by concern:

- **`test_ai_provider_offline.py`** — the offline provider makes zero network calls and
  requires no API key (concrete enforcement of product principle 4), and every intent's
  template renders the exact facts present in its evidence dict.
- **`test_ai_provider_anthropic.py`** — the real provider's every `httpx.post` call is
  mocked (`unittest.mock.patch`); this suite never makes a live network request. Covers
  availability checks and every failure mode (timeout, network error, 401, 429, other
  4xx/5xx, malformed response body).
- **`test_ai_factory.py`** — disabled/offline/anthropic-misconfigured/anthropic-configured
  provider selection, confirming no silent fallback.
- **`test_ai_evidence.py`** — each evidence builder's determinism, size caps, and error
  handling (unknown column, missing/malformed `ml_result`).
- **`test_ai_routing.py`** — every deterministic-question pattern, including the
  word-boundary column-matching fix (a column name must not match as a substring of another
  word) and non-numeric/undefined-statistic fallthrough.
- **`test_ai_service.py`** — orchestration via a `FakeProvider` test double: disabled mode,
  an unavailable provider, provider runtime errors, and successful generation all still
  return `computed`.
- **`test_ai_grounding.py`** (the mandatory grounding-guarantee suite,
  `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md` section 22) — proves that a
  `FakeProvider` returning deliberately fabricated/wrong text (wrong row count, wrong mean,
  wrong correlation coefficient, wrong ML metric, wrong duplicate count) never changes the
  corresponding `computed` value; also proves determinism across repeated calls and that a
  provider cannot inject new keys into `computed`. This is the concrete, structurally
  enforced form of product principle 3, going beyond "the template can only interpolate
  known fields" to an end-to-end proof at the response-contract level.
- **`test_ai_security.py`** — prompt-injection attempts via both column names and cell
  values are proven to reach a provider only as inert evidence data, never as an
  instruction; API keys never appear in the `/ai/status` response; evidence sent to a
  provider is proven bounded (no raw per-row values, sample values capped, wide-dataset
  column lists capped).
- **`test_ai_api.py`** — full API integration tests for `/ai/status`, `/analyze`, `/query`,
  including structured error paths (`column_not_found`, `ml_result_required`,
  `dataset_not_found`) and OpenAPI schema registration.

A UI test will later confirm the computed vs. AI-generated visual distinction
(`UI_UX_SPEC.md` §4.6) actually renders as two structurally different blocks, not just
different CSS classes with identical layout — deferred to Phase 06/07 (frontend), out of
scope for the backend-only Phase 05.

## 7. Test Data & Fixtures Policy

- Only synthetic/fixture datasets are committed to the repository — small, purpose-built to
  exercise specific behaviors (nulls, duplicates, outliers, mixed types), never real or
  personally identifiable data. ✅ CONFIRMED.
- Real user-uploaded datasets (via `data/uploads/`, `ARCHITECTURE.md`) are always gitignored
  and never committed.

## 8. CI Integration

🟡 ASSUMED split (finalized Phase 08, "Testing, Docker & Deployment"):
- **On every push/PR:** lint, unit tests, integration tests, build — fast enough to run on
  every change.
- **Manual/pre-release (Phase 08 release checklist):** full end-to-end suite, performance
  checks — slower, not required on every commit.

## 9. Relationship to Phase Prompts

This document defines **how**; each `01_PHASES/<phase>/PHASE_PROMPT.md`'s own testing
section defines **what**, and is the authoritative checklist an agent must satisfy before
that phase's `DEFINITION_OF_DONE.md` gate passes. If the two ever appear to conflict, the
phase prompt's specific requirement wins for that phase, and the conflict should be flagged
and this document updated.

---
*Related: [../01_PHASES/](../01_PHASES/) ·
[../00_AGENT_CONTROL/DEFINITION_OF_DONE.md](../00_AGENT_CONTROL/DEFINITION_OF_DONE.md) ·
[ARCHITECTURE.md](ARCHITECTURE.md)*
