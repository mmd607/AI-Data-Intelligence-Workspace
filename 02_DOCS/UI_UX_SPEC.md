# UI/UX Specification — Data Intelligence Universe

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED

This document defines the visual and interaction language for the product, and in
particular the "Data Intelligence Universe" — the primary interface. It exists because
`01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md` describes the Universe concept in a
single paragraph; this file gives that phase (and Phase 06's 2D chrome) enough concrete
detail to implement against without inventing requirements.

---

## 1. Design Philosophy

✅ CONFIRMED — the product must feel **premium, minimal, dark, sophisticated, cinematic,
technically oriented, and subtle rather than flashy.**

**Explicit anti-goals** (✅ CONFIRMED, treated as hard constraints checked at Phase 07
acceptance):

- No generic admin-dashboard appearance (card grids of KPI tiles, default component-library
  look).
- No excessive neon / oversaturated glow.
- No cartoonish 3D (rounded mascot-like shapes, toy materials).
- No unnecessary 3D objects — every object in the scene must represent real data or a real
  relationship (product principle 6).
- No visual effect that reduces usability (motion that obscures text, bloom that reduces
  contrast, camera moves that disorient) — directly echoes the ZIP's own Phase 07 rule:
  "The 3D layer must enhance usability rather than become a gimmick."

## 2. Visual Language

- **Color:** a dark neutral base (near-black to deep charcoal, not pure `#000`) with **one**
  primary accent color and **one** secondary accent, used sparingly for interactive/active
  states, not decoration. Semantic states (good/warning/critical data-quality signals) use
  desaturated, low-luminance variants of standard hues (green/amber/red) rather than
  saturated neon equivalents. Exact hex values are ❓ OPEN QUESTION, deferred to a dedicated
  design-token pass at the start of Phase 07 (🟡 ASSUMED to live in a design-tokens file /
  Tailwind config, not hardcoded per component).
- **Typography:** a modern technical sans-serif for UI text (🟡 ASSUMED: Inter or
  comparable) and a monospace face for all numeric/data values (🟡 ASSUMED: JetBrains Mono
  or comparable) — the sans/mono split reinforces "technically oriented" and gives computed
  numbers a distinct visual identity from prose, reinforcing the computed-vs-AI-explanation
  separation (product principle 2) typographically as well as structurally (§4.6).
- **Depth & elevation:** subtle blur/translucency (glass-panel effect) and layering, not
  heavy borders or drop shadows.
- **Iconography:** minimal line icons, single stroke weight, no filled/cartoon icon sets.

## 3. Layout Overview

- **Primary surface:** the 3D Universe, full-viewport by default.
- **Left sidebar (collapsible):** workspace/dataset list, upload entry point.
- **Right inspector panel (slide-in, appears on node selection):** detail content for the
  selected node, including the computed/AI-generated split (§4.6).
- **Top bar (minimal):** app identity, active dataset name, global status (e.g. processing
  indicator), an AI-mode on/off toggle (making product principle 4 visible in the UI).
- **Fallback 2D "List/Table" view:** the same information architecture as the Universe,
  presented as a plain table + detail panel, for accessibility, low-end hardware, and
  no-WebGL environments (§4.7). This is **not optional** — it must reach full feature parity
  for data access; only the spatial/navigational metaphor is lost. ✅ BUILT (Phase 06) —
  `frontend/src/features/`, real backend data throughout the upload → overview → quality →
  analytics → ML → AI flow; Phase 07 adds the 3D layer on top/in front of it.

## 4. The Data Intelligence Universe

### 4.1 Node Taxonomy & Hierarchy

✅ CONFIRMED node types, matching the ZIP's own Phase 07 concept diagram, arranged as a
hybrid hierarchy/graph (a hub of orbiting nodes, not a flat unstructured graph):

- **Dataset node** — the center of the scene (the ZIP's diagram centers "DATASET"; when
  multiple datasets exist, each gets its own dataset-centered cluster reachable from a
  workspace-level entry point).
- Orbiting the dataset node:
  - **Data Profile node**
  - **Data Quality node**
  - **Statistics node**
  - **Visualization node**
  - **ML node**
  - **AI Insights node**

This hierarchy is intentional: it keeps the scene legible (principle 6) by grouping related
information spatially rather than scattering all nodes into one undifferentiated graph.

### 4.2 Node Visual States

Every node must implement all of the following states (✅ CONFIRMED minimum state machine):

| State | Visual treatment |
|---|---|
| Idle/default | Subtle floating motion (small-amplitude, staggered per node so the scene doesn't move in lockstep), soft ambient glow at low intensity |
| Hover | Slight scale increase, brightened glow, readable label/tooltip appears |
| Selected/active | Inspector panel opens; connecting lines to this node highlight/brighten; camera may ease toward it (§4.4) |
| Loading/processing | Pulse animation — while a computation (e.g. ML training) is in flight for that node; visually distinct from "error" |
| Error/warning | Desaturated red/amber accent (not neon), consistent with §2's semantic-color rule; never the sole indicator — always paired with text in the panel |
| Disabled/empty | Dimmed/low-opacity — used when a node's data doesn't exist yet (e.g. no ML run performed) |

### 4.3 Connections

Animated lines/curves connect the dataset node to each child node, with a subtle
directional flow animation indicating the relationship is "alive," not static geometry
(reinforces principle 6). Non-selected connections are dimmed; connections touching the
selected/hovered node are highlighted. ✅ CONFIRMED.

### 4.4 Camera & Motion

- Orbit controls with damping (smooth, not snappy) for free navigation. ✅ CONFIRMED
  ("smooth camera movement" per the ZIP's Phase 07 prompt).
- Selecting a node triggers an eased camera transition toward a framing of that node (a
  "focus" state), with a clear way back to the overview — 🟡 ASSUMED exact interaction,
  finalized in Phase 07, but the *requirement* for a focus/overview cycle is ✅ CONFIRMED.
- No aggressive parallax, no camera shake, no auto-rotating "showcase" mode by default —
  motion must always be either user-driven or state-driven (loading/selection), never
  ambient spectacle.

### 4.5 Interaction Model

- Click: select node → opens inspector panel (matches ZIP's "Clicking a node opens its
  corresponding detailed workspace").
- Drag: orbit camera. Scroll/pinch: zoom. Hover: tooltip + highlight/focus state.
- Double-click empty space / explicit "back" control: return to overview framing.
- Keyboard: full tab-order navigation through nodes as an accessibility fallback (§5) —
  ✅ CONFIRMED as a requirement, exact key bindings 🟡 ASSUMED, finalized in Phase 07.

### 4.6 Information Panels — Computed vs. AI-Generated

✅ CONFIRMED, directly enforcing product principle 2 and the data-flow contract in
`ARCHITECTURE.md`:

Every panel that can show an AI explanation renders it in a **visually distinct block**: a
subtler background tint, a small mode-attribution label ("AI explanation — offline" or "AI
explanation — <provider name>"), positioned below/subordinate to the computed data it
explains — never interleaved in a way that could be mistaken for a computed value. Computed
values use the monospace numeric treatment from §2; AI-generated text uses standard
sans-serif prose. The two must never share a visual style.

### 4.7 Performance & Graceful Degradation

✅ CONFIRMED as a hard requirement, directly matching the ZIP's own Phase 07 "Performance"
section ("Avoid unnecessary re-renders, huge particle counts, and expensive effects.
Measure/inspect performance and document trade-offs") and "responsive fallback for
low-performance devices":

- **Capability detection** on load determines a performance tier:
  - **High tier:** full effect set (subtle bloom only if it doesn't reduce text contrast,
    full node count, smooth 60fps target).
  - **Mid tier:** reduced particle/effect count, no post-processing, same node count.
  - **Low tier / no WebGL:** automatic fallback to the 2D List/Table view (§3), same data,
    same inspector panels — zero functional loss, only the spatial metaphor is dropped.
- Heavy post-processing (depth-of-field, screen-space reflections, heavy bloom) is not used
  by default at any tier. Exact tier thresholds are 🟡 ASSUMED, finalized with real
  profiling in Phase 07.

## 5. Accessibility

- ✅ CONFIRMED — `prefers-reduced-motion` is respected: floating/pulse/camera-ease
  animations are reduced or removed when set (matches the ZIP's "reduced-motion
  consideration").
- ✅ CONFIRMED — the 2D fallback view (§3, §4.7) is the accessibility path for
  screen-reader and keyboard-only users where the 3D scene itself cannot reasonably be made
  screen-reader-accessible; it must not be a degraded second-class experience for *data
  access*, only for the spatial metaphor.
- ✅ CONFIRMED — text contrast in all 2D UI (sidebar, panels, top bar) meets WCAG AA at
  minimum, independent of the 3D scene's own aesthetic treatment.

## 6. Responsive Behavior

Desktop is the primary target. 🟡 ASSUMED — tablet gets a reduced-complexity 3D scene (mid
tier by default); mobile defaults straight to the 2D List/Table view with the 3D Universe
available on-demand rather than automatically, given the poor fit between orbit controls
and small touchscreens. Finalized in Phase 07.

## 7. Component Inventory (2D chrome)

Standard components needed across phases (buttons, cards, tables, upload dropzone, modals,
toasts, tabs, form inputs). ✅ CONFIRMED (Phase 06) — hand-built with Tailwind utility
classes, not a third-party component library, consistent with the "not generic dashboard"
requirement. `frontend/src/components/` (`Card`, `Badge`, `StatValue`, `Tabs`,
`LoadingSkeleton`/`ErrorState`/`EmptyState`) covers what Phase 06 needed; modals/toasts
were not required by this phase's flow and remain unbuilt until a concrete need exists.
Full design-token finalization (exact palette/typography) remains Phase 07's job per §9.

## 8. States & Empty/Error/Loading Design Requirements

Every data-bearing view must define: an empty state (clear guidance on the next action, e.g.
"Upload a dataset to begin"), a loading state (skeleton, not a spinner-only block, where
feasible), and an error state (clear, non-alarming language, an actionable next step) —
✅ CONFIRMED as a requirement (matches the ZIP's Phase 06 "clear loading/error/empty states"
frontend principle); concrete designs produced per-phase as each view is built.

## 9. Open Questions

- ❓ Exact color palette (hex values) — Phase 07.
- ❓ Exact typography choice confirmation (Inter/JetBrains Mono are placeholders) — Phase 07.
- ❓ Exact motion timing/easing curves — Phase 07.
- ❓ Exact performance-tier thresholds — Phase 07.
- ❓ Mobile 3D-on-demand interaction details — Phase 07.

None of the above block Phases 01–06; they must be resolved before Phase 07's acceptance
criteria can be checked off.

---
*Related: [PRODUCT_SPEC.md](PRODUCT_SPEC.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[../01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md](../01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md) ·
[../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md](../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md)*
