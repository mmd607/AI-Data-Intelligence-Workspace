# Decisions Log

The full Architecture Decision Record log for this project. `ARCHITECTURE.md`'s "Decision
Log" section points here. Use [`TEMPLATE.md`](TEMPLATE.md) for new entries. Entries are
numbered sequentially and never renumbered; a superseded decision is marked as such, not
deleted.

---

# ADR-R001: Control-System Reconciliation

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** Pre-Phase-01 (reconciliation, not a build phase)

## Context
Earlier in this session, before this `00_AGENT_CONTROL/` / `01_PHASES/` / `02_DOCS/` /
`03_TEMPLATES/` structure was introduced, a standalone foundation was written directly at
the repository root: flat markdown files (`PROJECT_SPEC.md`, `ARCHITECTURE.md`,
`UI_UX_SPEC.md`, `AGENTS.md`, `PHASE_INDEX.md`, `PROGRESS.md`, `GIT_WORKFLOW.md`,
`TESTING_STRATEGY.md`, `DEVELOPMENT_RULES.md`, `docs/`), defining a **12-phase (00–11)**
roadmap and a **trunk-based** Git workflow (direct, phase-gated commits to `main`, no
mandatory branch-per-phase). It was never committed.

The human then supplied `AI_Data_Intelligence_Agent_Build_System.zip`, a separate, deliberately
prepared control system with an **8-phase (01–08)** roadmap, a `00_AGENT_CONTROL/` +
`01_PHASES/` + `02_DOCS/` + `03_TEMPLATES/` layout, and a **strict branch-per-phase** Git
workflow (`main` never touched by the agent, human-only merges). This created two
competing, incompatible control systems in the same uncommitted working tree.

## Decision
The ZIP's system is authoritative in full: its 8-phase roadmap, its folder layout, its
strict Git workflow (branch-per-phase, no direct `main` work, no agent-initiated merges).
The richer content already written in the earlier draft (detailed per-technology stack
evaluation, the full product-principles table, the complete 3D Universe UI/UX
specification, the testing methodology, and the seeded architecture decisions below) was
migrated into the ZIP's file locations rather than discarded, remapped from the old
12-phase numbering to the ZIP's 8-phase numbering. The old root-level duplicate files were
then removed once migration was verified. See the session's Foundation Review / audit /
reconciliation report for the full before/after file inventory.

## Alternatives Considered
- **Keep the 12-phase/trunk-based system, treat the ZIP as reference only** — rejected: the
  human explicitly designated the ZIP as authoritative.
- **Run both systems side by side** — rejected outright: two competing project-control
  systems is exactly the failure mode this reconciliation exists to prevent.

## Consequences
Every phase reference elsewhere in this documentation set uses the ZIP's 8-phase numbering
(`PHASE_01_FOUNDATION` … `PHASE_08_TESTING_DOCKER_DEPLOYMENT`) and its branch-per-phase Git
model. No document in this repository should reference a 9th–12th phase, a `Phase 00`, or a
trunk-based/direct-to-`main` workflow going forward — if one is found, it is a leftover from
the pre-reconciliation draft and must be fixed.

## Related
All ADRs below (renumbered phase references); `00_AGENT_CONTROL/PROJECT_STATE.md`;
`00_AGENT_CONTROL/GIT_WORKFLOW.md`.

---

# ADR-001: Frontend Stack

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION

## Context
The product's primary interface is a premium, cinematic 3D experience (the "Data
Intelligence Universe"), layered with a data-heavy 2D UI (panels, charts, tables). The
stack needs to support both without fighting itself.

## Decision
React + TypeScript + Vite + Tailwind CSS + React Three Fiber + Three.js, as proposed by the
human and the ZIP's `AGENT_MASTER_INSTRUCTIONS.md` architecture baseline.

## Alternatives Considered
- **Next.js instead of Vite** — rejected: no SSR/SEO requirement exists for a local-first,
  single-page data tool; Vite's dev loop is faster for this use case.
- **A 3D engine other than Three.js/R3F** — not seriously evaluated; R3F is the standard,
  best-supported React binding and keeps the 3D scene declarative.

## Consequences
TypeScript end-to-end (paired with Pydantic on the backend) lets the computed/AI-generated
response contract be type-checked, not just conventionally followed.

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Frontend".

---

# ADR-002: Data Visualization Library

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED — to be confirmed with real evidence in Phase 03
**Phase:** PHASE_03_DATA_PROFILING_VISUALIZATION

## Context
The product must avoid a "generic admin dashboard" look (product principle 5). Chart
library choice materially affects achievable visual identity.

## Decision
visx (Airbnb), a low-level primitives library built on D3, chosen over higher-level
pre-styled chart libraries.

## Alternatives Considered
- **Recharts** — set aside for now: fast to use, but its default visual identity is
  difficult to fully de-genericize; theming ceiling too low for the "premium" bar.
- **Nivo** — same reasoning as Recharts.
- **Observable Plot** — documented fallback if visx's lower-level API proves too slow to
  implement against in Phase 03's timeframe.

## Consequences
More implementation effort per chart than a pre-styled library, in exchange for full visual
control. If Phase 03 shows this tradeoff isn't worth it, switch to the documented fallback
and update this ADR (mark superseded, not edited in place).

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Frontend";
`../../01_PHASES/PHASE_03_DATA_PROFILING_VISUALIZATION/PHASE_PROMPT.md`.

---

# ADR-003: Backend Stack

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION

## Context
The backend must perform real, reproducible data profiling/statistics/ML computation and
expose it over a typed API.

## Decision
Python + FastAPI + Pydantic + Pandas + NumPy + scikit-learn, as proposed by the human and
the ZIP's architecture baseline.

## Alternatives Considered
Not seriously evaluated against non-Python stacks — Python's data/ML ecosystem is the
standard, correct fit for this product's core computation needs.

## Consequences
Pydantic models become the literal mechanism enforcing the computed/AI-generated response
contract (product principle 2).

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Backend".

---

# ADR-004: XGBoost Inclusion

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED (deferred) — final decision due Phase 04
**Phase:** PHASE_04_ML_ENGINE

## Context
The ZIP's own Phase 04 prompt says: "Prefer scikit-learn. Use XGBoost only when it
materially adds value and is justified." Adding it means a heavier, non-sklearn-native
dependency for a niche scikit-learn's own gradient-boosting implementations may already
partially cover.

## Decision
Not adopted at foundation time. Phase 04 must run a concrete evaluation (accuracy delta on
real fixture datasets vs. dependency cost) and record a final decision here.

## Alternatives Considered
- **Adopt now** — rejected: no evidence yet that it's needed; violates the
  dependency-addition policy (`AGENT_MASTER_INSTRUCTIONS.md`) which requires justification,
  not default inclusion.
- **Never adopt** — not decided either; left genuinely open pending Phase 04 evidence.

## Consequences
Phase 04 acceptance criteria explicitly require this decision to be finalized before the
phase can close.

## Related
`../ARCHITECTURE.md` "Stack Evaluation — Backend";
`../../01_PHASES/PHASE_04_ML_ENGINE/PHASE_PROMPT.md`.

---

# ADR-005: Dataset & Metadata Storage

**Date:** 2026-09-17
**Status:** ❓ OPEN QUESTION — final decision due Phase 02
**Phase:** PHASE_02_DATA_INGESTION

## Context
v1 is single-user, local-first. Uploaded files need storage; profiling/ML results need
somewhere to live too.

## Decision (working assumption only)
Raw files on the filesystem (`data/uploads/`, gitignored); metadata/results as JSON sidecar
files, not a database, for v1.

## Alternatives Considered
- **SQLite via SQLAlchemy** — the natural next step if cross-dataset querying/filtering
  becomes a real requirement; not yet justified for a single-workspace v1.

## Consequences
If Phase 02 finds the sidecar-file approach insufficient (e.g. for concurrent read/write
safety, or listing/filtering performance), this ADR is superseded by a new one adopting
SQLite, and `ARCHITECTURE.md` is updated accordingly.

## Related
`../ARCHITECTURE.md` "Data Storage";
`../../01_PHASES/PHASE_02_DATA_INGESTION/PHASE_PROMPT.md`.

---

# ADR-006: AI Mode Abstraction

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_05_AI_ANALYTICS

## Context
Product principles 3 and 4 (and the ZIP's own Phase 05 "Core rule": "The LLM is an
interpreter, not the source of truth") require the app to work fully without an external
LLM, and require AI output to never introduce new numeric claims.

## Decision
A pluggable AI-mode interface with an offline deterministic template-based implementation
as the default, and a real LLM provider as strictly opt-in. Every mode receives only the
already-computed JSON payload, never raw data, and is instructed to explain, not compute.

## Alternatives Considered
- **LLM-only, no offline mode** — rejected outright: directly violates principle 4 and the
  ZIP's own Phase 05 "Fallback" requirement.
- **Free-form prompting with raw data access** — rejected: cannot structurally guarantee
  principle 3; the offline-template + computed-payload-only approach can.

## Consequences
This is the concrete mechanism `../TESTING_STRATEGY.md` §6 tests against.

## Related
`../ARCHITECTURE.md` "AI Mode Abstraction";
`../../01_PHASES/PHASE_05_AI_ANALYTICS/PHASE_PROMPT.md`.

---

# ADR-007: Real LLM Provider Choice

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED — final decision due Phase 05
**Phase:** PHASE_05_AI_ANALYTICS

## Context
The AI mode abstraction (ADR-006) needs at least one real implementation beyond the offline
default to be meaningfully "optional" rather than theoretical.

## Decision (working assumption only)
Anthropic Claude, given the project's existing tooling context — not a hard architectural
commitment, since the interface is provider-agnostic by design.

## Alternatives Considered
Not yet evaluated in depth; OpenAI/other providers remain viable given the abstraction
layer makes switching low-cost.

## Consequences
None yet — the interface does not depend on this choice.

## Related
`../ARCHITECTURE.md` "AI Mode Abstraction".

---

# ADR-008: 3D Scene State Management

**Date:** 2026-09-17
**Status:** 🟡 ASSUMED — final decision due Phase 07
**Phase:** PHASE_07_3D_UNIVERSE_UI

## Context
The 3D scene has frequently-updating state (hover, selection, camera focus) that must not
cause unnecessary re-renders across the whole component tree.

## Decision (working assumption only)
Zustand, chosen over React Context for its more granular subscription model.

## Alternatives Considered
- **React Context** — set aside as a default: prone to over-rendering for
  frequently-updating state unless carefully split.

## Consequences
None yet — confirmed with real implementation experience in Phase 07.

## Related
`../ARCHITECTURE.md` "3D Interaction & State";
`../../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md`.

---

# ADR-009: Infrastructure — Docker, CI, Health Checks

**Date:** 2026-09-17
**Status:** ✅ CONFIRMED
**Phase:** PHASE_01_FOUNDATION (health checks) / PHASE_08_TESTING_DOCKER_DEPLOYMENT (full Docker/CI)

## Context
`PRODUCT_SPEC.md` success criteria require a one-command local run (`docker compose up`)
and CI enforcement of the phase-gated workflow.

## Decision
Multi-stage Docker images per service, docker-compose for orchestration, GitHub Actions for
CI, `/health` endpoint(s) wired into compose health checks. A backend health endpoint is
introduced as early as Phase 01; full Docker/CI implementation is Phase 08.

## Alternatives Considered
Not seriously evaluated against alternatives — standard, low-risk infrastructure tooling
with no product-specific tradeoff to weigh.

## Consequences
None beyond the standard Docker/CI maintenance surface.

## Related
`../ARCHITECTURE.md` "Infrastructure";
`../../01_PHASES/PHASE_01_FOUNDATION/PHASE_PROMPT.md`;
`../../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md`.
