# Product Specification — Data Intelligence Universe

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED (see
`00_AGENT_CONTROL/AGENT_MASTER_INSTRUCTIONS.md` for how these are used).

## Product
A portfolio-grade end-to-end Data Intelligence platform. ✅ CONFIRMED.

## Input
Initially CSV datasets. ✅ CONFIRMED (JSON/Parquet may be considered later — see §Open
Questions; not required for v1).

## Core pipeline
Ingest → Validate → Profile → Visualize → ML → AI Explain → Explore in 3D.

## Vision

The product's differentiator is not the analytics themselves (profiling, statistics, and
baseline ML are well-understood problems) but the **experience**: a cinematic, spatial "Data
Intelligence Universe" that makes the relationships between a dataset, its quality, its
statistics, its features, and its models legible at a glance — replacing the generic
tab-and-table admin-dashboard pattern common in this space.

## Product Principles

These are binding constraints on every phase, not aspirational goals. Every phase's
acceptance criteria (`01_PHASES/*/PHASE_PROMPT.md`) is checked against this list.

| # | Principle | Why it matters | Practical implication |
|---|---|---|---|
| 1 | Evidence over assumptions | Prevents the product from asserting things it cannot support | Every displayed number must be traceable to a computation, not a guess |
| 2 | Computed data must always be distinguishable from AI-generated explanations | Trust — users must never mistake a narrative gloss for a fact | API responses and UI must carry an explicit `source: computed \| ai_generated` distinction everywhere AI text appears (`ARCHITECTURE.md` §Data Flow) |
| 3 | AI must never invent statistical or ML results | The AI layer is a narrator, not a calculator | AI providers only ever receive already-computed values and are instructed to explain, never to produce new numbers — enforced at the API boundary, not just by prompting (Phase 05) |
| 4 | The application must remain useful without an external LLM provider | Local-first, no vendor lock-in, works offline/no API key | A deterministic, offline "explainer" is the default AI mode; a real LLM provider is opt-in (`ARCHITECTURE.md`, Phase 05) |
| 5 | The frontend should feel like a professional data-intelligence product, not a generic dashboard | Differentiator; portfolio quality bar | See `UI_UX_SPEC.md` for the full visual language |
| 6 | The 3D experience must improve navigation and understanding, not exist merely as decoration | Avoids "3D for its own sake," a known failure mode of novelty UIs | Every 3D node/connection must map to a real data entity or relationship; no orphan decorative geometry (`UI_UX_SPEC.md`) |
| 7 | The system should be modular and extensible | Long project lifespan across 8 phases, built incrementally | Strict module boundaries (`ARCHITECTURE.md`, `AGENT_MASTER_INSTRUCTIONS.md`) |
| 8 | Every implementation phase must be independently testable | Enables safe incremental, agent-driven development | Every phase in `01_PHASES/` defines its own test requirements and acceptance criteria |
| 9 | Every completed phase must have documented acceptance criteria | Prevents "done" from being subjective | See each `PHASE_PROMPT.md`; criteria are written before the phase starts |
| 10 | The repository must always preserve a clear development history | Traceability, safe rollback, portfolio narrative | See `GIT_WORKFLOW.md` — no history rewriting, phase branches, human-controlled merges |

## User Outcome

A user can upload a dataset and understand:
- what is inside it;
- whether it has quality issues;
- key statistics;
- useful relationships/patterns;
- baseline ML results when applicable;
- an AI-written explanation grounded in actual calculations.

## Target Users / Personas

- 🟡 ASSUMED — **Primary persona:** a data-literate individual (analyst, data scientist,
  technical PM, or a portfolio reviewer/recruiter evaluating the project) who wants a fast,
  visually impressive first look at an unfamiliar dataset — quality, shape, and a baseline
  model — without writing code.
- 🟡 ASSUMED — **Secondary persona:** the project owner themself, using it as a portfolio
  centerpiece demonstrating full-stack + applied ML + advanced frontend capability.
- ❓ OPEN QUESTION — an enterprise/team persona (multi-user, auth, shared workspaces) is not
  requested anywhere in the brief and is treated as out of scope (see Non-Goals) unless
  stated otherwise later.

## Signature Interface

The 3D "Data Intelligence Universe" acts as the navigation layer for analytical modules
rather than replacing conventional dashboards. See `UI_UX_SPEC.md` for the complete
specification (node taxonomy, states, interactions, performance tiers, and the mandatory 2D
fallback).

## Core Capabilities (v1 Scope)

1. **Dataset upload & management** — upload CSV (and, if feasible, other tabular formats),
   validate, store, list/retrieve. ✅ CONFIRMED. (Phase 02)
2. **Data quality inspection** — deterministic, rule-based profiling: nulls, types,
   duplicates, distributions, outlier flags, a transparent/versioned quality score.
   ✅ CONFIRMED. (Phase 03)
3. **Statistics & visualization exploration** — descriptive statistics, correlations,
   distributions, rendered as charts, always labeled as computed. ✅ CONFIRMED. (Phase 03)
4. **ML baseline analysis** — scikit-learn baseline model(s) against a user-selected target
   column, with real evaluation metrics. ✅ CONFIRMED. XGBoost inclusion is 🟡 ASSUMED
   (conditional, evaluated on real evidence). (Phase 04)
5. **AI explanation layer (optional)** — plain-language explanation of already-computed
   results, via a pluggable mode (offline deterministic default, real LLM opt-in).
   ✅ CONFIRMED, with principles 3/4 as hard constraints. (Phase 05)
6. **3D "Data Intelligence Universe" interface** — the primary navigation surface; see
   `UI_UX_SPEC.md`. ✅ CONFIRMED as the primary interface, with a mandatory 2D fallback for
   accessibility and low-end hardware. (Phase 07)

## Non-Goals

Explicitly **not** part of this project unless a human amends this document:

- autonomous claims unsupported by data;
- fake AI-generated statistics;
- replacing rigorous analysis with decorative 3D effects;
- forcing ML on datasets where it is inappropriate;
- multi-user accounts, authentication, authorization, or team/sharing features;
- real-time collaborative editing or live filesystem watching;
- AutoML / hyperparameter tuning UI / deep learning;
- native desktop packaging (Electron, Tauri);
- data warehouse/database connectors (file upload only for v1);
- production-scale hosting/multi-tenancy decisions — infrastructure is prepared
  (Docker/CI, Phase 08) but a live public deployment is not a v1 requirement;
- streaming/very-large-dataset (beyond memory) processing — v1 targets datasets that fit
  comfortably in memory on a single machine (🟡 ASSUMED, exact ceiling set in Phase 02).

## Success Criteria (Definition of Done for v1)

v1 is complete when, from a clean clone:

1. A user can start the app locally (`docker compose up`, Phase 08) with no manual fixes.
2. A user can upload a real dataset and see, end-to-end, through the 3D Universe: its
   quality profile, its statistics/visualizations, and a baseline ML result — all real
   computed data, no mock data in the primary flow.
3. Disabling the AI layer entirely leaves the product fully functional (principle 4).
4. Every number shown as "computed" is reproducible from the same input data.
5. Every AI-generated explanation is visually and structurally distinguishable from
   computed data (principle 2), and provably does not introduce new numeric claims not
   present in the computed payload (principle 3).
6. The 3D interface meets the anti-goals in `UI_UX_SPEC.md` (no neon, no cartoonish 3D,
   nothing purely decorative) and degrades gracefully on low-end hardware / no WebGL.
7. CI passes (lint, unit, integration, build) per `TESTING_STRATEGY.md`.
8. All 8 phases in `01_PHASES/` are marked complete in `00_AGENT_CONTROL/PROJECT_STATE.md`.

## Key Product Constraints

- Local-first by default: no dataset content leaves the machine unless the user explicitly
  enables a real AI provider (principle 4).
- No secrets/API keys ever committed to the repository.
- The product must never silently fabricate a value where data is missing — missing
  evidence is surfaced as `N/A`/`unknown`, never a zero or a guess (principle 1).

## Glossary

| Term | Meaning |
|---|---|
| Universe | The primary 3D visualization surface (see `UI_UX_SPEC.md`) |
| Node | A single entity in the Universe (dataset, quality, statistics, visualization, ML, AI insight) |
| Computed data | Any value produced by deterministic code (pandas/NumPy/scikit-learn) |
| AI-generated content | Any text produced by an AI mode (offline or real LLM) — narrative only, never a new number |
| Phase gate | The set of conditions (`DEFINITION_OF_DONE.md`) that must pass before a phase's commit/push |

## Open Questions

- ❓ Exact per-dataset size/row limits for v1 (Phase 02).
- ❓ Whether a lightweight persistence layer (SQLite) is needed for metadata, or whether
  filesystem + JSON sidecars suffice for v1 (Phase 02; see `ARCHITECTURE.md`).
- ❓ Whether XGBoost is included or scikit-learn baselines alone are sufficient (Phase 04).
- ❓ Whether any enterprise/multi-user persona should be supported (currently out of scope).

---
*Related: [ARCHITECTURE.md](ARCHITECTURE.md) · [UI_UX_SPEC.md](UI_UX_SPEC.md) ·
[TESTING_STRATEGY.md](TESTING_STRATEGY.md) · [../01_PHASES/](../01_PHASES/) ·
[decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md)*
