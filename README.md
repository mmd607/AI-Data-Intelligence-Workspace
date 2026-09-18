# AI Data Intelligence Workspace

A local-first data intelligence tool: upload a CSV, get a deterministic quality/statistics
profile, explore correlations and distributions, train a transparent baseline ML model, and
ask grounded questions of an AI layer that only ever narrates numbers the system actually
computed — it never invents a statistic, a correlation, or a metric. The interactive part is
the **Data Intelligence Universe**, a 3D visualization of a dataset and everything computed
about it, with a full-parity 2D fallback for when 3D isn't appropriate (no WebGL, a small
screen, or a user preference).

This repository is also a controlled, phase-by-phase build system for an AI coding agent
(Claude Code, Cursor Agent, or equivalent) — see "Agent build system," below, if that's what
brought you here. If you just want to run the app, skip to "Quick Start."

## What it does

1. **Upload** a CSV dataset.
2. **Ingest & validate** — row/column counts, dtypes, missing/duplicate detection, size and
   file-type limits, clear errors on malformed input.
3. **Profile** — per-column statistics (numeric/categorical/datetime), a rule-based data-
   quality findings engine (missing values, duplicates, constant columns, high-cardinality
   categoricals, mixed types, and more).
4. **Explore** — pairwise correlation (with an explicit "not enough data" status when
   applicable, never a fabricated number) and histogram distributions.
5. **Visualize** in the 3D Universe or its 2D-table equivalent — same underlying data,
   presented two ways.
6. **Run baseline ML** — logistic regression / random forest / linear regression / ridge,
   picked from a fixed, transparent model registry; real train/test metrics, never a claim
   that one model is universally "best."
7. **Ask grounded AI questions** — the AI layer (offline by default, no network calls, no
   API key needed; optionally a real Anthropic model) explains what was already computed. A
   structural grounding guarantee (enforced by tests, not just a prompt) means a
   misbehaving or fabricating provider can never alter the underlying computed facts a
   response reports.

## Quick Start (Docker)

```bash
docker compose up --build
```

Frontend: `http://localhost:8080` · Backend: `http://localhost:8000/health`. No
configuration required — see [`02_DOCS/DEPLOYMENT.md`](02_DOCS/DEPLOYMENT.md) for options
(ports, enabling the real AI provider, data persistence) and what was and wasn't locally
verified for the Docker path in this environment.

## Documentation Map

| Doc | Covers |
|---|---|
| [`02_DOCS/PRODUCT_SPEC.md`](02_DOCS/PRODUCT_SPEC.md) | Product principles, scope, non-goals |
| [`02_DOCS/ARCHITECTURE.md`](02_DOCS/ARCHITECTURE.md) | System design, module boundaries |
| [`02_DOCS/UI_UX_SPEC.md`](02_DOCS/UI_UX_SPEC.md) | Design tokens, the Universe's visual encodings |
| [`02_DOCS/TESTING_STRATEGY.md`](02_DOCS/TESTING_STRATEGY.md) | Testing approach + real, measured coverage numbers |
| [`02_DOCS/SECURITY_NOTES.md`](02_DOCS/SECURITY_NOTES.md) | Threat model, findings, fixes, honestly-recorded limitations |
| [`02_DOCS/DEPLOYMENT.md`](02_DOCS/DEPLOYMENT.md) | Docker/Compose configuration and verification status |
| [`02_DOCS/decisions/DECISIONS_LOG.md`](02_DOCS/decisions/DECISIONS_LOG.md) | Every architecture decision, with alternatives considered |

## Limitations (Honest, Not Hidden)

- **No authentication/authorization** — local-first, single-user by design (see
  `02_DOCS/PRODUCT_SPEC.md` "Non-Goals"), not multi-tenant-safe.
- **CSV only** — no Excel/Parquet/database connectors in this version.
- **Baseline ML only** — a fixed model registry, no hyperparameter tuning, no AutoML; every
  result labels itself as a baseline, never as production-ready.
- **AI is optional and narration-only** — off by default network-wise (`offline` provider);
  when a real provider is configured it can only narrate already-computed facts, never
  originate a new one (see `SECURITY_NOTES.md` §2.4).
- **No public deployment target** — Docker/Compose is a local/self-hosted production-like
  path, not a hosting decision; see `02_DOCS/DEPLOYMENT.md` §9.
- **Docker build/runtime was not locally verified in the agent's own environment** during
  Phase 08 (Docker isn't installed there) — verified instead by a dedicated CI job on every
  push. See `SECURITY_NOTES.md` §4 for the full accounting.

## Agent Build System

The sections below describe how this repository was built — a controlled, phase-by-phase
process for an AI coding agent. If you're a human running the app, everything above this
point is what you need; the rest is process documentation.

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

## Local Development

Backend and frontend run as two separate local processes — no Docker is required for
day-to-day development (hot reload on both sides is faster than a container rebuild loop).
Docker/Compose (see "Quick Start" above and `02_DOCS/DEPLOYMENT.md`) is the release/
production-like path, finalized in Phase 08.

### Backend (Python + FastAPI)

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env            # optional — sane defaults work without it
uvicorn app.main:app --reload --port 8000
```

- Health check: `http://localhost:8000/health`
- Interactive API docs: `http://localhost:8000/docs`
- Tests: `pytest`
- Lint: `ruff check .`

### Frontend (React + TypeScript + Vite)

```bash
cd frontend
npm install
cp .env.example .env.local      # optional — defaults to http://localhost:8000
npm run dev
```

- App: `http://localhost:5173`
- Tests: `npm run test`
- Lint: `npm run lint`
- Production build: `npm run build`

Start the backend first (or at least before checking the frontend's connectivity badge) —
the frontend shell displays live backend connectivity status on load.
