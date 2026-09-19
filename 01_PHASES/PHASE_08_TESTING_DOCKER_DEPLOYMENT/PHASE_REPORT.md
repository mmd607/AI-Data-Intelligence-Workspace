# Phase Report

## Phase
PHASE_08_TESTING_DOCKER_DEPLOYMENT — executed under the branch name
`phase/08-final-productization-release`, per explicit human instruction this session
(superseding this folder's own `PHASE_PROMPT.md` §"Branch" naming;
`00_AGENT_CONTROL/GIT_WORKFLOW.md`'s general rule — human approval controls branch
naming/scope — takes precedence here). The human's own brief for this session
substantially expanded this phase's scope beyond `PHASE_PROMPT.md`'s original
testing/Docker/deployment checklist into a full engineering, product, UX, and security
audit of everything built in Phases 01–07, not just new Phase 08 infrastructure. Both are
recorded as the same Phase 08 in `PROJECT_STATE.md` — this is not a Phase 09.

## Date
2026-09-18

## Branch
`phase/08-final-productization-release` (branched from `phase/07-3d-data-intelligence-universe`,
which was already clean and fully merged-forward from `main` per Phase 07's own report).

## What was built

**Audit performed first, before any code change** (per this phase's own "do not start by
coding" instruction): read every file under `00_AGENT_CONTROL/`, every `01_PHASES/*/PHASE_PROMPT.md`,
all of `02_DOCS/`; established a real baseline (342/342 backend tests passing once run
against the project's own pinned `.venv` — see "Bugs found and fixed" below for why an
ambient global interpreter showed 3 false failures; 131/131 frontend tests passing;
`ruff`/`eslint`/`tsc`/`vite build` all clean) before changing anything.

- **Security:** found and fixed a real dataset-id path-traversal gap
  (`app/ingestion/storage.py`) — confirmed exploitable with `TestClient` before the fix,
  disproven the same way after it. Full write-up: `02_DOCS/SECURITY_NOTES.md`,
  `02_DOCS/decisions/DECISIONS_LOG.md` ADR-018. Reviewed and confirmed-safe: upload
  filename handling, CORS config, secret handling (`SecretStr`, no key ever logged or
  returned), prompt-injection defenses (already structurally enforced by Phase 05's
  grounding-guarantee test suite, re-verified not re-litigated), global exception handling
  (never leaks a stack trace or internal path).
- **Product/UX audit performed live**, against real running backend + frontend dev
  servers (not just reading code): full golden-path walkthrough — upload → overview →
  quality (including its empty-state) → analytics (correlation + distributions) → ML
  (target-suitability validation, then a real training run with two different models) → AI
  Insights (grounded explanation of the trained model + a real deterministic Q&A exchange)
  → 3D Universe (confirmed a real WebGL canvas is rendering, not just present in the DOM)
  → 2D fallback (confirmed full data parity with 3D) → an unknown dataset id (clean
  structured error + "Try again," no stack trace) → an unknown route (redirects home, by
  design, `App.tsx`'s catch-all route). Found and fixed one real, concrete product-polish
  bug: internal "in this phase" development-process language had leaked into five
  user-facing strings (the upload page's helper text and validation error, a backend
  file-type error message, an ML `unavailable_metrics` reason, and an ML `limitations`
  entry) — an actual user would have no idea what "this phase" refers to. Reworded to
  ordinary product language; no test asserted on the old exact text, so nothing broke.
- **Dockerization (new):** `backend/Dockerfile` (multi-stage, `python:3.12-slim`, non-root,
  installs only from the pinned `requirements.txt`, `/health`-based `HEALTHCHECK`);
  `frontend/Dockerfile` (multi-stage, `node:20-slim` build → `nginxinc/nginx-unprivileged`
  runtime, non-root by construction, SPA-fallback `nginx.conf`); root `docker-compose.yml`
  (named volume for upload persistence, backend health-gated frontend startup, AI-provider
  env pass-through); `.dockerignore` for both services; root `.env.example` documenting
  Compose-level overrides. Full rationale and alternatives considered:
  `02_DOCS/decisions/DECISIONS_LOG.md` ADR-017.
- **CI/CD:** removed a stray, unrelated `python-publish.yml` (a default GitHub-template
  PyPI-publish workflow that had nothing to do with this project — dead debris, found
  during the cleanup pass). Added `.github/workflows/ci.yml`: `backend` (ruff + pytest),
  `frontend` (eslint + vitest + typecheck/build), `docker` (depends on both, then a real
  `docker compose up -d --build` + health-check-poll + HTTP verification of both services,
  always dumps logs, always tears down).
- **Documentation:** created `02_DOCS/SECURITY_NOTES.md` (threat model, every finding,
  every fix, every honestly-recorded limitation) and `02_DOCS/DEPLOYMENT.md` (Docker quick
  start, configuration reference, the one real constraint of a static SPA's build-time env
  vars, verification status); updated `02_DOCS/TESTING_STRATEGY.md` with real Phase 08
  numbers (§2, §8) and `02_DOCS/decisions/DECISIONS_LOG.md` (ADR-017, ADR-018); rewrote
  the top of `README.md` from a purely agent-process document into one that also explains
  the product, gives a Docker quick start, links every doc, and states limitations up
  front — kept the "Agent Build System" process content below it, not replaced.

## Architecture decisions
- ADR-017 (Docker/CI execution — concrete image choices, networking, persistence, the CI
  Docker-verification job, the stray-workflow removal).
- ADR-018 (dataset-id path-traversal hardening — character-allowlist validation at the
  single `StorageService._dataset_dir` choke point, chosen over a stricter UUID4 regex
  specifically to avoid breaking existing unit tests that legitimately use simple test ids).

Both in `02_DOCS/decisions/DECISIONS_LOG.md`, full context/alternatives-considered there.

## Files/components added or changed

**Added:** `backend/Dockerfile`, `backend/.dockerignore`, `frontend/Dockerfile`,
`frontend/.dockerignore`, `frontend/nginx.conf`, `docker-compose.yml`, `.env.example`,
`.github/workflows/ci.yml`, `02_DOCS/SECURITY_NOTES.md`, `02_DOCS/DEPLOYMENT.md`, this
phase report.

**Changed:** `backend/app/ingestion/storage.py` (path-traversal fix), `backend/tests/test_datasets_api.py`
(new `TestDatasetIdTraversal` class, 4 tests), `backend/app/ingestion/validation.py`,
`backend/app/ml/evaluation.py`, `backend/app/ml/schemas.py`, `backend/app/ml/training.py`,
`frontend/src/features/upload/UploadPage.tsx` (all six: "in this phase" copy fixes),
`README.md`, `02_DOCS/TESTING_STRATEGY.md`, `02_DOCS/decisions/DECISIONS_LOG.md`.

**Removed:** `.github/workflows/python-publish.yml` (dead, unrelated debris).

No product/domain modules were added — consistent with this phase's "Non-Goals" (no new
features).

## Tests/checks

| Check | Command | Result |
|---|---|---|
| Backend tests | `pytest -q` (project's own pinned `.venv`) | **346 passed**, 0 failed |
| Backend coverage | `pytest -q --cov=app --cov-report=term-missing` | **99% overall**; `app/ingestion/storage.py` at **100%** (the file this phase's security fix touched) |
| Backend lint | `ruff check .` | All checks passed |
| Frontend tests | `npm run test -- --run` | **131 passed**, 0 failed (unchanged from Phase 07 — no regression) |
| Frontend lint | `npm run lint` (`--max-warnings 0`) | Clean |
| Frontend typecheck + build | `npm run build` (`tsc --noEmit && vite build`) | Clean; main bundle ~215 KB, Universe chunk ~1.05 MB lazy-loaded (unchanged from Phase 07) |
| Live end-to-end walkthrough | Real backend + frontend dev servers, built-in browser | Upload → Overview → Quality (empty state) → Analytics → ML (validation + 2 real training runs) → AI Insights (grounded explanation + real Q&A) → 3D Universe (real WebGL canvas confirmed) → 2D fallback (full parity confirmed) → dataset-not-found error path → unknown-route redirect — all verified working, zero console errors observed |
| Path-traversal regression | `pytest -q tests/test_datasets_api.py::TestDatasetIdTraversal` | 4/4 passed (new this phase) |
| Docker build/runtime | *(see "Known limitations")* | **Not locally verified** — Docker is not installed in the agent's execution environment. Manually re-reviewed every Dockerfile/compose line for correctness; substituted a local `uvicorn` smoke test under the exact non-`--reload` invocation the backend `Dockerfile`'s `CMD` uses (`/health` → 200, `/docs` → 200). The `docker` job in `.github/workflows/ci.yml` performs the actual build+runtime verification on GitHub Actions' Docker-equipped runners on every push — check that CI run before treating Docker support as proven. |
| Environment-drift finding | *(diagnostic, not a fix)* | The ambient global Python interpreter had `pandas 3.0.5` installed vs. the pinned `pandas==2.2.3`, causing 3 false test failures before this phase's baseline was established against the project's own `.venv`. Documented in `SECURITY_NOTES.md` §2.7 as exactly the class of problem Docker's pinned-dependency image build eliminates. |

## Known limitations
- Docker images could not be build/runtime-verified in this environment (no Docker
  installed here) — see the table above and `SECURITY_NOTES.md` §4 / ADR-017 for the full,
  honest accounting and what CI does instead.
- No authentication/authorization, no rate limiting, no multi-tenant isolation — explicitly
  out of scope per `PRODUCT_SPEC.md` "Non-Goals," documented in `SECURITY_NOTES.md` §4 and
  the new `README.md` "Limitations" section.
- Upload size enforcement reads the full body into memory (via FastAPI's
  `UploadFile.read()`, itself backed by a spooled temp file above ~1 MB) before validating
  size — acceptable at the current 50 MB default for a local-first tool; would need
  streaming validation before raising that default significantly. Documented in
  `SECURITY_NOTES.md` §4.
- No public cloud deployment target selected — deliberately out of scope, documented in
  `02_DOCS/DEPLOYMENT.md` §9.

## Git
Branch: `phase/08-final-productization-release`
Commits: one commit, message `feat: complete final productization and release hardening`
— see `git log -1` on this branch for its hash (per this phase's own instructions, the
commit cannot self-reference its own hash).
Remote branch: `origin/phase/08-final-productization-release` (pushed after this commit).

## Next phase
None planned. This is the final phase in `00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md`'s
phase order. The human decides if/when to merge this branch into `main` and whether to cut
a release tag (`00_AGENT_CONTROL/GIT_WORKFLOW.md` "Tagging").

---

## Addendum (2026-09-19) — Desktop-First Polish Pass

A follow-up human instruction on this same branch asked for a dedicated desktop-quality
pass (Windows/macOS/Linux desktop, 1080p/1440p/4K, mouse/keyboard, browser compatibility).
Performed live against real dev servers in a real browser, not just by reading code.

**Found and fixed:** `WorkspaceLayout.tsx` capped every workspace page, including the 3D
Universe, at a fixed `max-w-5xl` (1024px) regardless of monitor size — on a 1440p/4K
display the flagship 3D visualization was no larger than on a 1280px laptop. Fixed by
removing the Universe route's content max-width entirely (scales continuously with the
viewport, bounded only by responsive padding) while giving the text/table 2D pages a wider
but still-capped reading width (`max-w-6xl` → `max-w-[1400px]` at `2xl`). Also widened
`AnalyticsPage`'s distribution grid to 3 columns at `xl`, and added one global
`focus-visible` rule in `index.css` — no interactive element anywhere had an explicit focus
style before this. Full rationale and alternatives considered: `decisions/DECISIONS_LOG.md`
ADR-019; UX-facing detail: `UI_UX_SPEC.md` §5–6.

**Verified live, not just read from code:** resized a real browser through 1280×720,
1366×768, 1440×900, 1920×1080, 2560×1440, and 3840×2160 on the Universe and 2D pages — no
horizontal overflow at any size (`scrollWidth`/`clientWidth` checked explicitly at 4K); 3D
mouse/keyboard interactions (orbit-drag, scroll-zoom, click-to-select via a real raycast hit
confirmed against the dataset-core mesh, hover cursor change, Escape-to-close, "Reset View,"
search-to-focus with real computed feature stats displayed) all confirmed working, before
and after the layout change; keyboard `Tab` order and the new focus ring confirmed visible
on real elements (the workspace back-link/tab-bar and the Universe HUD's "Reset View"
button).

**Investigated, confirmed not a bug:** duplicate `GET` requests observed in the network
panel (each dataset endpoint fetched twice on page load) are `React.StrictMode`'s standard,
dev-only intentional double-invocation of effects (`main.tsx`) — a known, harmless React 18
diagnostic behavior, not a production duplicate-request bug; not "fixed" because there is
nothing to fix. A one-time `THREE.WebGLRenderer: Context Lost` console message coincided
with several rapid viewport resizes in immediate succession during this test pass itself
(not something a real user does) and did not recur under normal use.

**Tests/checks after this pass:** frontend — 131/131 tests passing (unchanged), `eslint`
clean, `tsc --noEmit && vite build` clean. No backend changes in this addendum.

**Honest limitation:** cross-browser verification (Chrome/Edge/Firefox/Safari) was not
performed — only the one Chromium-based automated browser available in this environment was
tested. No claim is made about Firefox/Safari/Edge-specific behavior; the CSS/layout used
(Tailwind utilities, standard flex/grid, no vendor-prefixed or bleeding-edge features) is
broadly compatible, but that is a reasonable expectation, not a verified fact.
