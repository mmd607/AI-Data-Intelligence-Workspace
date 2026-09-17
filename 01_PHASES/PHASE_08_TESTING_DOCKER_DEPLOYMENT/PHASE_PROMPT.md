# PHASE 08 — TESTING, DOCKER & DEPLOYMENT

## Objective
Make the application reproducible and release-ready.

## Tasks
- backend test suite hardening;
- frontend test suite hardening;
- API integration tests;
- end-to-end smoke test;
- Dockerfiles;
- Docker Compose;
- environment configuration;
- health checks;
- production build;
- logging;
- basic security hardening;
- documentation for local and production-like startup.

## Release checks
Verify:
- fresh clone can be built;
- services start;
- health checks pass;
- core CSV workflow works;
- 3D UI loads;
- AI fallback works;
- no secrets are present;
- tests pass.

## Output
Release checklist + final architecture docs + phase report + state update.
Push final phase branch. Do not merge into main automatically.

---

## Scope

Two closely related concerns, both required for release readiness: (1) **raising test
coverage and hardening reliability/security** across everything built in Phases 01–07
(coverage targets, security checklist, error boundaries, adversarial-input handling), and
(2) **finalizing Docker/CI/CD** (multi-stage Dockerfiles, docker-compose, GitHub Actions,
health checks wired into orchestration) so the "Release checks" above all pass from a
genuinely clean clone.

## Non-Goals

New product features; an actual public cloud deployment/hosting purchase decision
(documented as a follow-up, not required for this phase's release bar, per
`../../02_DOCS/PRODUCT_SPEC.md` "Non-Goals").

## Inputs

The fully integrated, tested application through Phase 07.

## Outputs

A documented coverage report; a documented, resolved security checklist; `docker compose
up` producing a fully working application from a clean clone; a CI pipeline green on every
push/PR.

## Files/Components Expected

Additional test files across `backend/` and `frontend/` (no new product modules);
`Dockerfile`s (frontend + backend, multi-stage), `docker-compose.yml`,
`.github/workflows/ci.yml`, `.env.example`.

## Testing Requirements

Coverage thresholds from `../../02_DOCS/TESTING_STRATEGY.md` met; security checklist items
each verified by an actual test or documented manual check (not merely claimed); CI
pipeline green on a genuinely clean clone/checkout; a smoke test that `docker compose up`
yields a healthy stack (`/health` returns OK for the backend, the frontend serves); the
full "Release checks" list above, each verified individually and recorded, not assumed.

## Acceptance Criteria

Defined coverage targets met; no open critical/high security findings; the app handles
malformed/hostile input (oversized files, malicious filenames, malformed JSON, wrong
content-types) without crashing or leaking internal details in error responses; a fresh
clone, following only documented steps, plus `docker compose up`, yields a working
application with no manual fixes; every item in "Release checks" above passes and is
recorded in the phase report.

## Documentation Requirements

Create `../../02_DOCS/SECURITY_NOTES.md`; update `../../02_DOCS/TESTING_STRATEGY.md` with
actual achieved coverage numbers; document local and production-like startup (root
`README.md` or a new `../../02_DOCS/DEPLOYMENT.md`); do a final consistency pass across all
of `02_DOCS/` and `00_AGENT_CONTROL/`, confirming every 🟡 ASSUMED / ❓ OPEN QUESTION marker
introduced across the project is either resolved or explicitly and consciously re-deferred
with reasoning — none left silently dangling, matching the rigor the human required at the
foundation-reconciliation stage of this project.

## Branch

`phase/08-testing-docker-deployment`. Child branches as needed:
`backend/08-testing-docker-deployment-*`, `frontend/08-testing-docker-deployment-*`,
`chore/08-testing-docker-deployment-*`.

## Rollback Considerations

Hardening changes are generally additive (new tests, new guards); if a specific fix
regresses legitimate behavior, revert that fix individually and record why in
`../../02_DOCS/decisions/DECISIONS_LOG.md`. Infrastructure changes (Docker/CI) are isolated
from application code; reverting them does not affect app behavior outside the
containerized/CI environment.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. This is the final phase — push the branch and
stop; the human decides when/how to merge into `main` and, if desired, cut a release tag
(`../../00_AGENT_CONTROL/GIT_WORKFLOW.md` "Tagging").
