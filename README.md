# AI Data Intelligence Workspace — Agent Build System

This repository is a controlled, phase-by-phase build system for an AI coding agent
(Claude Code, Cursor Agent, or equivalent).

## Product goal

Build an end-to-end Data Intelligence platform that can ingest a dataset such as CSV,
profile and validate it, calculate statistics, visualize data, run baseline ML analysis,
and use an AI layer to explain computed results without inventing numbers.

The final product should feel like a polished portfolio-grade application called
**Data Intelligence Universe** with a clean dark UI and interactive 3D data/analysis
visualization.

## Non-negotiable build rules

1. Read `00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md` before doing anything.
2. Read `00_AGENT_CONTROL/PROJECT_STATE.md` at the start of every session.
3. Build phases strictly in order.
4. Never skip a phase because it appears easy.
5. Never push directly to `main`.
6. Every phase must use its own branch.
7. Backend work must use `backend/*` branches; frontend work `frontend/*`;
   shared/integration work `integration/*`; docs/tooling `chore/*`.
8. Commit small, meaningful units of work.
9. Before a phase is marked complete: run tests, lint/type checks where applicable,
   update documentation, update PROJECT_STATE.md, and produce a phase report.
10. Push the completed branch to GitHub.
11. Do NOT merge automatically into `main`.
12. If a merge is required, create/use an integration branch and ask the human
    before merging anything into a protected/shared branch.
13. If credentials, secrets, OAuth, GitHub permissions, database credentials, API keys,
    or destructive commands are required, stop and ask the human.
14. Do not fabricate test results, metrics, screenshots, API responses, or model outputs.
15. Keep AI explanations grounded in values actually calculated by the system.

## Phase order

PHASE 01 Foundation
PHASE 02 Data Ingestion
PHASE 03 Data Profiling & Visualization
PHASE 04 ML Engine
PHASE 05 AI Analytics
PHASE 06 API + Frontend Integration
PHASE 07 3D Universe UI
PHASE 08 Testing + Docker + Deployment

The agent must not start the next phase until the current phase passes its completion gate.

## Repository map

```
00_AGENT_CONTROL/   Agent-facing operating rules — read this first, every session.
                     START_HERE.md · AGENT_MASTER_INSTRUCTIONS.md · PROJECT_STATE.md ·
                     GIT_WORKFLOW.md · DEFINITION_OF_DONE.md · PHASE_EXECUTION_TEMPLATE.md ·
                     BLOCKERS.md
01_PHASES/           One folder per phase, each with a PHASE_PROMPT.md defining that
                     phase's objective, scope, non-goals, inputs/outputs, implementation
                     guidance, tests, acceptance criteria, docs, branch, and rollback plan.
02_DOCS/             Product and architecture documentation.
                     PRODUCT_SPEC.md · ARCHITECTURE.md · UI_UX_SPEC.md · TESTING_STRATEGY.md ·
                     decisions/DECISIONS_LOG.md (architecture decision records)
03_TEMPLATES/        PHASE_REPORT_TEMPLATE.md · BLOCKER_TEMPLATE.md
```

This is the single, authoritative control system for the project — see
`02_DOCS/decisions/DECISIONS_LOG.md` (ADR-R001) for the record of how an earlier draft
foundation was reconciled into this structure. No other file or folder in this repository
defines a competing phase roadmap or Git workflow.
