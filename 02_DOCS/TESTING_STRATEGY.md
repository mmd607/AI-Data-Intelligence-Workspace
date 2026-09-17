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
  and measured for real in Phase 08. **Actual, measured (Phase 03):** `app/profiling/` —
  99% line coverage (`pytest --cov=app.profiling --cov-report=term-missing`); the one
  uncovered line is a provably-unreachable defensive guard in a private helper (its only
  caller already checks the same condition first) — left uncovered deliberately rather
  than adding a contrived test or stripping a harmless safety check — the goal is 100%
  coverage of the important logic paths, not meaningless coverage inflation.
- Fixture datasets (small, synthetic, engineered to have known properties — known null
  counts, known duplicates, known distributions) live under a test-fixtures directory
  (🟡 ASSUMED path: `backend/tests/fixtures/`), are checked into git (they contain no
  real/PII data by policy, §7), and are the basis for the ZIP's own Phase 02 requirement:
  "valid CSV, empty CSV, malformed CSV, missing values, duplicate rows, mixed types" test
  fixtures.

## 3. Frontend Tooling

- ✅ CONFIRMED — **Vitest** + **React Testing Library** for component/unit tests, matching
  the ZIP's own baseline ("Vitest/Playwright or equivalent for frontend").
- 🟡 ASSUMED — **Playwright** for end-to-end tests (from Phase 06 onward), covering the
  primary upload-to-Universe flow and the 2D fallback path.
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

- A test proves the **offline mode makes zero network calls** and requires no API key —
  matches the ZIP's own Phase 05 "Fallback" requirement ("The product should remain useful
  if no external LLM API is configured. Provide a clear local/mock mode for development and
  tests") and is the concrete enforcement of product principle 4.
- A test proves AI-generated explanation text **only references values present in the
  computed payload** it was constructed from — enforced structurally (the offline mode's
  templates can only interpolate known fields; the real-provider path is tested by
  verifying the prompt/context construction only ever includes the computed payload, not
  raw data) — the concrete enforcement of principle 3, matching the ZIP's own "prevent
  unsupported numerical claims" requirement.
- A UI test confirms the computed vs. AI-generated visual distinction (`UI_UX_SPEC.md`
  §4.6) actually renders as two structurally different blocks, not just different CSS
  classes with identical layout.

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
