# PHASE 01 — FOUNDATION

## Objective
Create the engineering foundation without prematurely building product features.

## Tasks
1. Inspect the repository and preserve existing useful work.
2. Establish the project structure for:
   - backend/
   - frontend/
   - tests/
   - docs/
3. Initialize FastAPI backend.
4. Initialize React + TypeScript frontend.
5. Establish environment/configuration handling.
6. Add `.gitignore`, README foundations, and developer setup instructions.
7. Add a backend health endpoint.
8. Add a frontend shell that can display backend connectivity status.
9. Establish testing infrastructure.
10. Establish a clean API/client boundary.
11. Add basic error handling and logging.
12. Ensure local startup is documented.

## UI requirement
The shell should already feel intentional and modern, but do not spend the phase
building the final 3D universe.

## Acceptance
- backend starts;
- frontend starts;
- health endpoint works;
- frontend can communicate with backend;
- tests run;
- structure is ready for future phases.

## Output
Create `PHASE_REPORT.md` describing architecture, commands, decisions, and limitations.

Then update PROJECT_STATE, commit, and push the phase branch. Do not merge.

---

## Scope

Stand up a minimal, runnable skeleton for both frontend and backend, with no real product
features, proving the toolchain works end-to-end. Toolchain choices follow
`../../02_DOCS/ARCHITECTURE.md` (React + TypeScript + Vite + Tailwind + React Three Fiber /
Three.js + Framer Motion on the frontend; Python + FastAPI + Pydantic + Pandas/NumPy +
scikit-learn on the backend). A minimal Docker skeleton may optionally be started here
(🟡 ASSUMED optional) but full Docker/CI is Phase 08's responsibility, not this phase's.

## Non-Goals

No dataset upload, no profiling/stats/ML, no real 3D Universe content (an empty/placeholder
R3F canvas is acceptable to prove the render pipeline — the full Universe is Phase 07), no
full CI pipeline required yet (an optional skeleton is fine; full CI is Phase 08).

## Inputs

`../../02_DOCS/ARCHITECTURE.md` stack decisions; the existing repository state (README only
at the time this phase starts).

## Outputs

A working `npm run dev` (frontend) and a working `uvicorn` run (backend), both documented
in the root `README.md`.

## Files/Components Expected

`frontend/` (package.json, vite/tailwind/tsconfig, `src/main.tsx`, `src/App.tsx`,
`src/api-client/` boundary module per `../../02_DOCS/ARCHITECTURE.md` "Module Boundaries");
`backend/` (pyproject/requirements, `app/main.py`, `app/api/health.py`).

## Testing Requirements

Frontend build passes (`vite build`); backend `/health` returns `200` with an expected JSON
shape; lint passes on both sides. See `../../02_DOCS/TESTING_STRATEGY.md` for tooling
(Vitest/pytest) — this phase's bar is "the harness works," not coverage depth.

## Documentation Requirements

Update `../../02_DOCS/ARCHITECTURE.md` if the scaffold surfaces a decision not yet
recorded (with a matching entry in `../../02_DOCS/decisions/DECISIONS_LOG.md`); update root
`README.md` with actual run instructions; update `../../00_AGENT_CONTROL/PROJECT_STATE.md`.

## Branch

`phase/01-foundation` (see `../../00_AGENT_CONTROL/GIT_WORKFLOW.md`). Child branches, if
needed: `backend/01-foundation-*`, `frontend/01-foundation-*`, `chore/01-foundation-*`.

## Rollback Considerations

Purely additive; reverting this phase's branch removes the scaffold cleanly with no
dependent code yet.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
