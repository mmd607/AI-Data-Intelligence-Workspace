# Definition of Done

A phase is complete only when ALL applicable conditions are true.

## Engineering

- implementation is present and organized;
- no known critical errors remain;
- public interfaces are documented;
- configuration is explicit;
- error handling exists for expected failure modes.

## Testing

- phase-specific tests pass;
- relevant existing tests pass;
- lint/type checks pass where configured;
- no test is disabled merely to obtain a green result.

Methodology, tooling, and coverage targets behind "phase-specific tests" are defined in
[`../02_DOCS/TESTING_STRATEGY.md`](../02_DOCS/TESTING_STRATEGY.md) — that document defines
*how* testing is done; each phase's own `PHASE_PROMPT.md` defines *what* is required for
that specific phase, and is the authoritative checklist for that phase's gate.

## Documentation

- README/docs updated where needed;
- architecture decisions documented (`../02_DOCS/decisions/DECISIONS_LOG.md`);
- phase report created;
- known limitations recorded.

## Git

- correct non-main branch used;
- meaningful commits created;
- branch pushed to GitHub;
- no secrets committed;
- PROJECT_STATE updated.

## Handoff

The agent must stop after the phase and state:
- what was built;
- tests/checks run;
- branch name;
- commit(s);
- push result;
- known limitations;
- next phase.

No automatic merge to main.

---
*Related: [AGENT_MASTER_INSTRUCTIONS.md](AGENT_MASTER_INSTRUCTIONS.md) ·
[../02_DOCS/TESTING_STRATEGY.md](../02_DOCS/TESTING_STRATEGY.md) ·
[../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md](../03_TEMPLATES/PHASE_REPORT_TEMPLATE.md)*
