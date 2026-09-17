# PHASE 06 — API + FRONTEND INTEGRATION

## Objective
Connect the analytical backend to a polished frontend workflow.

## UX flow
Design a coherent journey:
1. landing/dashboard;
2. dataset input;
3. ingestion status;
4. dataset overview;
5. profiling;
6. visualization;
7. ML analysis;
8. AI insights.

## Frontend principles
- clean dark visual system;
- strong typography;
- responsive layout;
- subtle motion;
- clear loading/error/empty states;
- accessible interactions;
- reusable components;
- no visual clutter.

## Technical
- typed API client;
- consistent data models;
- loading/error boundaries;
- caching/state strategy where justified;
- route structure;
- no business calculations duplicated in UI.

## Output
Integrated tests, frontend checks, documentation, phase report, state update, branch push.
No main merge.

---

## Scope

Replace any remaining fixture/mock data with real backend data across the full 2D
journey listed above, using the typed API client and component inventory defined in
`../../02_DOCS/ARCHITECTURE.md` "Module Boundaries" and `../../02_DOCS/UI_UX_SPEC.md` §3/§7.
This is the 2D chrome (List/Table view, panels, upload flow) that the 3D Universe (Phase 07)
will layer on top of — this phase's UI must reach full functional parity on its own, since
`../../02_DOCS/UI_UX_SPEC.md` §4.7 requires the 2D view to be a first-class fallback, not an
afterthought.

## Non-Goals

The 3D Universe scene itself (Phase 07); production infrastructure (Phase 08).

## Inputs

Phase 01–05 outputs.

## Outputs

A fully wired 2D application — no mock/fixture data remaining in the primary user flow
(upload → ingest → profile → stats → ML → AI insight, all real).

## Files/Components Expected

`frontend/src/api-client/` (typed from the backend's OpenAPI schema, per this phase's own
"typed API client" requirement); route/page components for each step of the UX flow;
`frontend/src/panels/` (shared with Phase 07).

## Testing Requirements

End-to-end tests (🟡 ASSUMED tool: Playwright per `../../02_DOCS/TESTING_STRATEGY.md`)
covering the full UX flow above; a contract test verifying the frontend's types match the
backend's current OpenAPI schema (catches drift); component tests for loading/error/empty
states per `../../02_DOCS/UI_UX_SPEC.md` §8.

## Acceptance Criteria

A user can upload a real dataset and move through every step of the UX flow with real
computed data throughout; no mock data remains in the primary flow; loading/error/empty
states all behave correctly against a real backend; "no business calculations duplicated in
UI" is verifiably true (values displayed are passed through from the API, never
recalculated client-side).

## Documentation Requirements

Verify `../../02_DOCS/PRODUCT_SPEC.md` "Success Criteria" against the real, integrated 2D
app; create `../../02_DOCS/API_CONTRACTS.md` as the finalized API contract reference.

## Branch

`phase/06-api-frontend-integration`. Child branches as needed:
`frontend/06-api-frontend-integration-*`, `integration/06-api-frontend-integration-*`.

## Rollback Considerations

If integration introduces a regression, the previous fixture-backed or partially-wired
state remains recoverable from git history on this phase's own branch; revert the specific
integration commit rather than patching around a broken state.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
