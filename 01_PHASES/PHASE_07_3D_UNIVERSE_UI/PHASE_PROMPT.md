# PHASE 07 — 3D DATA INTELLIGENCE UNIVERSE

## Objective
Create the signature 3D interface.

## Concept
The user sees a dark, premium, interactive 3D "Data Intelligence Universe".

A central dataset node can connect to:
- Data Profile
- Data Quality
- Statistics
- Visualizations
- ML
- AI Insights

Clicking a node opens its corresponding detailed workspace.

## UI/UX
The 3D layer must enhance usability rather than become a gimmick.

Include:
- smooth camera movement;
- hover/focus states;
- meaningful node hierarchy;
- readable labels;
- controlled particle/glow effects;
- subtle animations;
- reduced-motion consideration;
- responsive fallback for low-performance devices.

## Architecture
Keep 3D presentation separate from analytical business logic.
The scene must consume structured API data.

## Performance
Avoid unnecessary re-renders, huge particle counts, and expensive effects.
Measure/inspect performance and document trade-offs.

## Output
A portfolio-grade 3D interface integrated with real Phase 2–6 data.
Tests/checks, phase report, state update, commit, push. No main merge.

---

## Scope

Build the full 3D "Data Intelligence Universe" per `../../02_DOCS/UI_UX_SPEC.md` §4 — node
taxonomy, states, connections, camera behavior, performance tiers, and the 2D fallback
trigger — wired to the real backend data already integrated in Phase 06. This phase also
resolves every remaining open question in `../../02_DOCS/UI_UX_SPEC.md` §9 (exact color
palette, typography confirmation, motion timing, performance-tier thresholds, mobile
behavior), and closes out `../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-008 (3D state
management library).

## Non-Goals

Any new backend capability (this phase consumes Phase 02–05's APIs as-is); any change to
the underlying computed/AI-generated data — the 3D layer is presentation only, per this
phase's own "Architecture" section.

## Inputs

`../../02_DOCS/UI_UX_SPEC.md`; the fully integrated 2D application from Phase 06.

## Outputs

A navigable Universe scene, meeting the node/state/camera/performance requirements below,
with the 2D view (Phase 06) as its automatic, fully-functional fallback.

## Files/Components Expected

`frontend/src/universe/` (R3F scene, node components, camera, connection-line rendering),
`frontend/src/panels/` (computed-vs-AI-generated visual split per
`../../02_DOCS/UI_UX_SPEC.md` §4.6, extending Phase 06's panel shell), `frontend/src/state/`
(Zustand store per ADR-008), a design-tokens/Tailwind config update per
`../../02_DOCS/UI_UX_SPEC.md` §2/§7 decisions made in this phase.

## Testing Requirements

Component/unit tests for node state transitions (`../../02_DOCS/UI_UX_SPEC.md` §4.2); a
test of the performance-tier fallback logic under a mocked low-capability condition; a
`prefers-reduced-motion` behavior test (matches this phase's own "reduced-motion
consideration"); a manual visual-QA pass against `../../02_DOCS/UI_UX_SPEC.md` §1's
anti-goals checklist, documented as a recorded checklist result, not just "looks good."
Performance must be measured and trade-offs documented, per this phase's own "Performance"
section.

## Acceptance Criteria

The Universe renders and is navigable; every visible node maps to real data (nothing purely
decorative, per product principle 6); the scene automatically falls back to the 2D view
(Phase 06) under a simulated low-end/no-WebGL condition with no data/functionality loss;
the anti-goals checklist passes with no exceptions; camera movement is smooth, hover/focus
states are implemented, labels are readable — the concrete form of this phase's own
"UI/UX" bullet list.

## Documentation Requirements

Finalize `../../02_DOCS/UI_UX_SPEC.md` (all §9 open questions resolved or explicitly
re-deferred with reasoning); capture representative screenshots into a
`../../02_DOCS/screenshots/` folder; resolve ADR-008.

## Branch

`phase/07-3d-universe-ui`. Child branches as needed: `frontend/07-3d-universe-ui-*`.

## Rollback Considerations

The Universe is a UI-only layer on top of Phase 06's already-working 2D application;
reverting this phase's branch leaves the fully functional 2D app intact — this is precisely
why Phase 06 must reach full parity first.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
