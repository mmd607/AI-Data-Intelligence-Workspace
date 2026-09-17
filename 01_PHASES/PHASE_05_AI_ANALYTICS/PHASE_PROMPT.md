# PHASE 05 — AI ANALYTICS

## Objective
Add an AI explanation layer that explains computed analytics rather than inventing them.

## Core rule
The LLM is an interpreter, not the source of truth.

It must receive structured, verified results from the analytics/ML layers.

## Tasks
- define an analysis-result schema;
- create an AI context builder;
- create prompts with explicit grounding rules;
- generate natural-language explanations;
- distinguish facts, interpretations, and limitations;
- handle missing context;
- prevent unsupported numerical claims;
- expose AI output with provenance/context.

## Fallback
The product should remain useful if no external LLM API is configured.
Provide a clear local/mock mode for development and tests.

## Privacy
Do not send raw sensitive data to external services by default.
Document what leaves the system.

## Output
Tests for grounding behavior, documentation, phase report, state update, commit, push.
Do not merge.

---

## Scope

Implement the optional AI explanation feature per
`../../02_DOCS/decisions/DECISIONS_LOG.md` ADR-006/ADR-007 — the AI-mode interface, the
offline deterministic implementation (the "local/mock mode" required by this phase's own
"Fallback" section), the optional real LLM integration (🟡 ASSUMED Anthropic, finalized
here), API endpoint(s) for fetching an explanation, and an explicit on/off toggle in the UI
(`../../02_DOCS/UI_UX_SPEC.md` §3 top bar — wired for real once Phase 06 exists; the
backend capability and its tests are this phase's deliverable regardless of frontend
timing).

## Non-Goals

Any feature where the AI layer computes or decides a statistic/ML result — explicitly
forbidden by product principle 3, not merely discouraged. This phase explains Phase 04's
already-computed metrics; it never recomputes or adjusts them.

## Inputs

Phase 02–04 outputs (real computed payloads to explain).

## Outputs

Working AI explanations, offline by default, real-provider opt-in.

## Files/Components Expected

`backend/app/ai/` (mode interface + offline + real implementations),
`backend/app/api/explain.py`.

## Testing Requirements

"Tests for grounding behavior" (per this phase's own Output line) means concretely: a test
proving the offline mode makes zero network calls and requires no API key; a structural
test proving explanation output only references fields present in the computed payload it
was given (enforced at the template/prompt-construction level, verified by test, not just
asserted) — this is the concrete mechanism satisfying "prevent unsupported numerical
claims" above. See `../../02_DOCS/TESTING_STRATEGY.md` §6.

## Acceptance Criteria

The app is fully functional with the AI layer disabled; when enabled, every AI-generated
explanation is clearly attributed and never presented as a computed value; no dataset
content leaves the machine unless the user has explicitly enabled a real provider (this
phase's own "Privacy" requirement, and product principle 4).

## Documentation Requirements

Finalize `../../02_DOCS/ARCHITECTURE.md` "AI Mode Abstraction" and ADR-007 with the actual
provider integrated; cross-reference `../../02_DOCS/PRODUCT_SPEC.md` principles 3 and 4 as
satisfied, naming the specific enforcement mechanism; document exactly what data leaves the
system and under what condition (this phase's own "Privacy" requirement).

## Branch

`phase/05-ai-analytics`. Child branches as needed: `backend/05-ai-analytics-*`.

## Rollback Considerations

The AI layer is fully optional and isolated; it can be disabled via configuration without
affecting any other part of the app, and reverting this phase's branch removes it cleanly.

## Completion Gate

`../../00_AGENT_CONTROL/DEFINITION_OF_DONE.md`, in full. Report using
`../../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md`. Do not merge into `main` — push the phase
branch and stop.
