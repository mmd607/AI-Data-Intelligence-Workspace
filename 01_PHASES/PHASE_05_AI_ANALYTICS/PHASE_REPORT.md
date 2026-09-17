# Phase Report

## Phase
PHASE 05 — AI Analytics

## Date
2026-09-18

## Branch
`phase/05-ai-analytics` (branched from `origin/main` at `48a1de5`, the human-merged,
Phase-04-included baseline)

## What was built

- **`backend/app/ai/`** — a module isolated from `ingestion/`/`profiling/`/`ml/`/`api/` per
  `02_DOCS/ARCHITECTURE.md` "Module Boundaries":
  - `errors.py` — `AIError` (independent of `IngestionError`/`ProfilingError`/`MLError`,
    identical `{code, message, status_code}` envelope).
  - `schemas.py` — every Pydantic request/response model, including the `computed` +
    `ai_explanation` envelope (`source: "ai_generated"` always labeled).
  - `provider.py` — the `AIProvider` ABC (`is_available()`, `generate()`) every provider
    implements, so the rest of the module never depends on a specific vendor.
  - `providers/offline.py` — the default, always-available, zero-network provider: pure
    string interpolation into fixed templates, one renderer per AI capability/intent.
  - `providers/anthropic_provider.py` — the real-LLM provider, calling Anthropic's Messages
    API directly via `httpx.post` (no SDK). Every failure mode (missing key, timeout,
    network error, 401, 429, other 4xx/5xx, malformed response body) is caught and
    re-raised as a structured `AIError`.
  - `factory.py` — `get_provider(settings)`: `disabled` → `None`, `anthropic` → an
    `AnthropicProvider` (even if misconfigured — no silent fallback to offline), otherwise
    → `OfflineProvider`.
  - `security.py` — `SYSTEM_INSTRUCTIONS` (the untrusted-data instruction hierarchy) and
    `build_user_prompt()`, structurally separating evidence-as-data from the request text.
  - `evidence.py` — deterministic, size-bounded evidence builders, one per capability, all
    reusing Phase 02-04's own already-computed output (never re-deriving a statistic).
  - `routing.py` — deterministic-first question routing: a fixed set of recognized question
    shapes resolved by direct lookup into Phase 02-04 output before any provider is
    consulted.
  - `service.py` — orchestration: builds evidence, calls the configured provider, assembles
    the response contract; never raises for a provider failure (`available: false` +
    `reason`), only for a genuinely bad request.
- **`backend/app/api/ai.py`** — 3 endpoints: `GET /api/v1/ai/status` (dataset-independent),
  `POST /api/v1/datasets/{id}/ai/analyze` (5 capabilities: dataset summary, quality
  explanation, column insight, correlation explanation, ML explanation), `POST
  /api/v1/datasets/{id}/ai/query` (grounded natural-language Q&A). Thin router only.
- **`backend/app/main.py`** — mounted both AI routers; registered an `AIError` exception
  handler (same structured envelope, independent class).
- **`backend/app/config.py`** — added `ai_provider`, `ai_model`, `ai_api_key` (Pydantic
  `SecretStr`, never logged), `ai_base_url`, `ai_timeout_seconds`.
- **Dependencies**: `httpx` promoted from dev-only to a runtime dependency (already used for
  the FastAPI test client since Phase 01 — no new dependency added for the real provider,
  per the phase prompt's "Dependency Discipline").
- **109 new backend tests** across 9 new test files (342 total, up from 233): provider
  tests (offline + mocked Anthropic), factory tests, evidence-builder tests, routing tests,
  service-orchestration tests (via a `FakeProvider` test double), the mandatory
  grounding-guarantee suite, security/injection tests, and full API integration tests.

## Architecture decisions

- **ADR-014 (new)**: records the provider interface, the no-silent-fallback policy, the
  choice of direct `httpx` calls over an SDK, the grounding-guarantee mechanism (evidence
  built and frozen before the provider is ever called), the word-boundary column-matching
  fix in question routing, the structural prompt-injection defense, data minimization
  caps, and secret handling.
- `02_DOCS/ARCHITECTURE.md` gained an "AI Analytics Architecture (Phase 05)" section (with
  "The Grounding Guarantee" and "Deterministic-First Question Routing" subsections) and its
  pre-existing "AI Mode Abstraction" section was updated from 🟡 ASSUMED to ✅ CONFIRMED now
  that Anthropic is the real, implemented provider.

## Files/components added or changed

New: 13 files under `backend/app/ai/` (including `providers/`), `backend/app/api/ai.py`, 9
new test files, `01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_REPORT.md`.
Changed: `backend/app/main.py` (router mounts + exception handler), `backend/app/config.py`
(AI settings), `backend/requirements.txt`/`requirements-dev.txt` (`httpx` promoted,
`pytest-cov` added), `backend/.env.example` (AI settings documented), `backend/tests/
conftest.py` (`FakeProvider` test double), `backend/pyproject.toml` (scoped `UP042` ignore
— see "Known limitations"), `02_DOCS/ARCHITECTURE.md`, `02_DOCS/TESTING_STRATEGY.md`,
`02_DOCS/decisions/DECISIONS_LOG.md` (ADR-014 added), `00_AGENT_CONTROL/PROJECT_STATE.md`.
Verified unchanged: `backend/app/ingestion/`, `backend/app/profiling/`, `backend/app/ml/`,
`backend/app/api/datasets.py`, `backend/app/api/profile.py`, `backend/app/api/ml.py` — no
Phase 02/03/04 regression (confirmed via the full 342-test suite, including every
pre-existing Phase 01-04 test, still passing, and live endpoint checks against a real
running server).

## Tests/checks

- Command: `ruff check .` → Result: **All checks passed.**
- Command: `pytest -q` → Result: **342 passed**, 0 failed, 0 skipped (109 new; all 233
  pre-existing Phase 01-04 tests still green — no regression).
- Command: `pytest --cov=app.ai --cov-report=term-missing` → Result: **100% line
  coverage** on `app/ai/`, with one documented, provably-unreachable defensive `raise` in
  `service._build_analyze_evidence` marked `# pragma: no cover` (guarded by a
  Pydantic-validated `AICapability` enum where every current member is already handled —
  see "Known limitations").
- Real server verification (not just automated tests): started `uvicorn` for real, uploaded
  a real fixture dataset (`ml_regression.csv`) via `curl -F`, trained a real ML model via
  the Phase 04 endpoint, then called every AI endpoint against the real running server:
  - `GET /api/v1/ai/status` → real `200`, `{"enabled": true, "provider": "offline",
    "available": true}` with zero configuration.
  - `POST .../ai/analyze` for all 5 capabilities (`dataset_summary`, `quality_explanation`,
    `column_insight`, `correlation_explanation`, `ml_explanation` fed the real trained
    model's result) → each returned real `computed` data exactly matching the real
    Phase 02-04 output, plus a grounded `ai_explanation`.
  - `POST .../ai/query` → a deterministic-lookup question ("How many rows are
    duplicated?") resolved directly from real data; an unsupported question (asking for an
    ML metric with no `ml_result` supplied) correctly returned `question_category:
    "unsupported"`.
  - Error paths verified live: `column_not_found` (404), `ml_result_required` (400),
    `dataset_not_found` (404).
  - `/openapi.json` listed all 3 new AI paths alongside the pre-existing ML/profiling/
    ingestion paths.
  - Phase 02/03/04 endpoints re-checked live on the same running server (`GET
    /api/v1/datasets`, `GET .../profile`) — both still `200`, confirming no regression.
  - Verification dataset removed from `data/uploads/` afterward.
- Confirmed no out-of-scope functionality introduced: no frontend or 3D UI code was added
  (Phase 05 is backend-only per the phase prompt).

## Known limitations

- One line in `service.py` (`_build_analyze_evidence`'s final `unsupported_capability`
  raise) is excluded from coverage via a documented `# pragma: no cover` rather than a
  contrived test — it is unreachable while `AICapability` is a Pydantic-validated enum with
  every current member already handled above it; it exists only to guard against a future
  enum addition being forgotten here.
- A pre-existing `UP042` Ruff finding (enums inheriting from both `str` and `Enum` rather
  than `StrEnum`) was discovered on `app/ml/schemas.py` and `app/profiling/schemas.py`
  during this phase's lint pass — unrelated to any Phase 05 change, most likely surfaced by
  a `ruff` version difference since those files were last verified lint-clean. Since
  str+Enum is the established, intentional project-wide pattern (needed for plain-string
  JSON/Pydantic serialization; `StrEnum` has different `__str__` formatting semantics that
  would risk changing already-shipped API output), a scoped `ignore = ["UP042"]` was added
  to `pyproject.toml` with an inline rationale, rather than modifying those out-of-scope
  Phase 03/04 files or leaving the whole suite non-lint-clean. `app/ai/schemas.py`'s own two
  enums follow the same pattern for consistency.
- The Anthropic provider is implemented and unit-tested (every HTTP call mocked) but has
  never been exercised against the real Anthropic API in this phase — per the phase
  prompt's explicit instruction never to depend on a live external LLM API in tests, and
  because no API key was provided. The offline provider is the verified, zero-configuration
  default; `available`/`reason` reporting for a misconfigured `anthropic` selection was
  verified instead (both in tests and structurally, since it's the same code path).
- No frontend consumes these endpoints yet (Phase 06 scope) — the computed/AI-generated
  visual distinction (`UI_UX_SPEC.md` §4.6) remains untested at the UI level until then.

## Git

Commits (on `phase/05-ai-analytics`): `6c04869` — `feat(phase-05): implement grounded AI
analytics layer`, followed by a small commit recording this hash back into this report and
`PROJECT_STATE.md` (unavoidable, same reason as prior phases).

Remote branch: `origin/phase/05-ai-analytics` — pushed and existence verified (see
completion message).

## Next phase

**PHASE 06 — API + Frontend Integration**
(`01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md`). Not started. Requires
explicit human approval before beginning.
