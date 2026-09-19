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

- **Color:** ✅ CONFIRMED (Phase 07, `frontend/tailwind.config.js`) — a dark neutral base
  (`surface.DEFAULT #0a0b0f`, `surface.raised #12151c`, not pure `#000`) with **one**
  primary accent (`accent.DEFAULT #6ee7ff`, cyan — unchanged since Phase 01) used for the
  dataset core and every deterministic domain/feature node, and **one** secondary accent
  (`accent.secondary #a78bfa`, violet) reserved *exclusively* for AI-generated/AI-sourced
  content (the AI Insights node and `panels/AIExplanationBlock.tsx`) — never used for
  computed data, a deliberate spatial reinforcement of product principle 2. Semantic
  good/warning/critical states reuse Tailwind's own desaturated emerald/amber/rose scales
  at low opacity (`components/Badge.tsx`'s Phase-06 pattern) rather than new hexes — already
  satisfies "desaturated, low-luminance, never saturated neon."
- **Typography:** ✅ CONFIRMED (Phase 07) — Inter (sans, UI text) and JetBrains Mono (mono,
  every numeric/data value), loaded via a Google Fonts `<link>` in `index.html` (no new npm
  dependency) and wired as `fontFamily.sans`/`fontFamily.mono` in `tailwind.config.js`. The
  sans/mono split reinforces "technically oriented" and gives computed numbers a distinct
  visual identity from prose, reinforcing the computed-vs-AI-explanation separation
  (product principle 2) typographically as well as structurally (§4.6).
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
- **Universe tab placement** — ✅ CONFIRMED (Phase 07): the Universe is a new "Universe" tab
  (`/datasets/:id/universe`), added as the *first* tab in `WorkspaceLayout`'s existing tab
  bar rather than replacing the Overview index route. This was a deliberate choice: it makes
  the Universe the immediately-discoverable flagship entry point (matching "primary surface"
  in spirit) while keeping every one of Phase 06's already-tested routes/behavior completely
  unchanged (zero regression risk) — the tab bar itself *is* the "2D fallback always
  reachable" requirement made concrete, since every other tab remains one click away at all
  times, from inside the Universe or outside it.

## 4. The Data Intelligence Universe

### 4.1 Node Taxonomy & Hierarchy

✅ CONFIRMED, finalized in Phase 07 (`frontend/src/universe/mapping.ts`) as a 4-level
hierarchy — an intentional extension of the ZIP's own 2-level concept diagram, made
concrete once the exact backend capabilities and real dataset structure were known to map
against (see ADR-016):

- **Level 1 — Dataset core** — the center of the scene, one per dataset workspace.
- **Level 2 — Domain nodes (5, fixed)**, orbiting the core: **Data Profile**, **Data
  Quality**, **Analytics**, **ML**, **AI Insights**. This is a deliberate, documented
  deviation from the ZIP's original 6-item list ("Statistics" and "Visualization" as
  separate nodes): Phase 06 already merged both into one `AnalyticsPage` (correlation +
  distribution) because there is no second, distinct backend capability behind them — two
  separate 3D nodes would either duplicate one domain's content or be partly decorative,
  which principle 6 forbids. Each domain node's `available`/`disabled` state reflects real
  data presence (e.g. the ML node is disabled until a model has actually been trained this
  session; the AI node reflects the real `AIStatusResponse.available`), never a guess.
- **Level 3 — Feature nodes**, one per dataset column, populating a ring around whichever
  domain node is focused (Profile or Analytics) rather than rendering all at once — the
  large-dataset strategy (§11). Visual encoding, fixed and documented (`universe/
  sceneTokens.ts`, the in-app `Legend`): **color** → `semantic_type`; **size** → normalized
  missingness (`null_percentage`) — the one, non-conflicting size meaning; a red tint marks
  a real `critical` quality finding on that column.
- **Level 4 — Correlation edges**, only from real `CorrelationResult.pairs` when
  `status === "computed"` (capped to the strongest 30 by `|coefficient|` — `ANALYTICS_
  PAIR_CAP`, ADR-016): edge thickness → normalized `|coefficient|`, edge color → sign,
  labeled "correlation" everywhere, never "cause." `insufficient_data` renders zero edges,
  with the real reason surfaced in the Analytics panel instead of a fabricated relationship.

This hierarchy keeps the scene legible (principle 6) by grouping related information
spatially and by progressive disclosure (a feature ring only appears once its domain is
focused) rather than scattering every node into one undifferentiated graph.

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

Dashed lines/curves connect the dataset node to each domain node and, within the Analytics
ring, feature nodes to each other via real correlation edges — reading as "a relationship,"
not static wireframe geometry (reinforces principle 6). Non-selected connections are
dimmed; connections touching the selected/hovered node are highlighted. ✅ CONFIRMED.

A per-frame animated dash-offset ("flow") was deliberately not built: the phase's own
"Performance" requirement ("avoid ... expensive effects") outweighs a purely decorative
animation here, and the hover/selection highlight already communicates "alive" without a
continuous render cost. Correlation edges themselves are not individually clickable in the
3D scene (thin `Line2` geometry is an unreliable raycast target at a distance); clicking the
Analytics domain node opens the same exact pairs/coefficients in 2D
(`panels/CorrelationPanel.tsx`) instead — a direct application of this phase's own
"3D is for spatial context, 2D is for precise information" principle, not a gap.

### 4.4 Camera & Motion

- Orbit controls with damping (smooth, not snappy) for free navigation. ✅ CONFIRMED
  ("smooth camera movement" per the ZIP's Phase 07 prompt) — implemented with
  `@react-three/drei`'s `CameraControls` (`universe/UniverseScene.tsx`), not raw
  `OrbitControls`: it gives built-in eased `setLookAt()` transitions and `minDistance`/
  `maxDistance` clamps in one component, which is exactly what "focus a node" and "prevent
  extreme zoom" (§12) need.
- Selecting a node triggers an eased camera transition toward a framing of that node (a
  "focus" state), with a clear way back to the overview via the "Reset View" HUD control —
  ✅ CONFIRMED (Phase 07). `smoothTime` is set to `0` (an instant cut, not eased) whenever
  `prefers-reduced-motion` is set, per §5/§27.
- No aggressive parallax, no camera shake, no auto-rotating "showcase" mode by default —
  motion must always be either user-driven or state-driven (loading/selection), never
  ambient spectacle.

### 4.5 Interaction Model

- Click: select (and focus/camera-ease toward) a node → opens the inspector panel (matches
  ZIP's "Clicking a node opens its corresponding detailed workspace"). ✅ BUILT.
- Drag: orbit camera (`CameraControls`). Scroll/pinch: zoom, clamped `minDistance`/
  `maxDistance` (§12). Hover: label + highlight state, plus the touching connection
  line(s) brighten. ✅ BUILT.
- Explicit "Reset View" HUD control returns to the overview framing — ✅ BUILT, chosen over
  "double-click empty space" as the *only* return-to-overview affordance: a single always-
  visible, discoverable, keyboard-reachable button is more accessible and less ambiguous
  than an empty-space gesture, and the phase brief itself explicitly asks for a visible
  "Reset View" control (§12).
- Keyboard: `Escape` clears the current selection/focus (closes the inspector panel) from
  anywhere on the page — ✅ BUILT. Full tab-order navigation *through individual 3D nodes*
  was not built — WebGL mesh objects have no native DOM tab stops, and building a parallel
  synthetic tab-order over Three.js objects was judged not worth the complexity given §5's
  own resolution: the 2D fallback view (search, filter chips, domain cards, a real
  `<table>`, every panel) is the actual, fully keyboard-and-screen-reader-navigable path for
  this data, exercised with real semantic HTML throughout — not a degraded second-class
  experience for *data access*, only for the spatial metaphor, exactly as §5 already commits
  to.

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

- **Capability detection** (`universe/tiers.ts::detectPerformanceTier`) on load determines
  a performance tier — ✅ CONFIRMED, concrete thresholds finalized in Phase 07 (ADR-016):
  - **High tier** (viewport ≥1280px, `navigator.hardwareConcurrency` >4 or unknown): full
    feature-node cap (60), a subtle starfield (`drei`'s `Stars`) and fog, `CameraControls`
    damping on.
  - **Mid tier** (768–1279px viewport, or `hardwareConcurrency` ≤4): feature-node cap
    lowered to 30, no starfield/fog, same node types and interactions.
  - **Low tier / no WebGL** (a throwaway `canvas.getContext('webgl')` probe fails, or
    viewport <768px by default — see §6): the Canvas never mounts at all; the 2D List/Table
    view (§3) renders instead, built from the identical `UniverseGraph` data — zero
    functional loss, only the spatial metaphor is dropped.
- No post-processing library is used at any tier (no `@react-three/postprocessing`
  dependency was added) — "glow" is achieved with `meshStandardMaterial` emissive
  intensity + the renderer's own tone mapping, which is enough to read as "premium" without
  the bloom/depth-of-field/screen-space-reflection cost the phase brief explicitly warns
  against.
- A render error thrown anywhere inside the Canvas is caught by `universe/
  UniverseErrorBoundary.tsx` and swaps in the same 2D fallback with an explanatory banner —
  the rest of the application (every other tab) is unaffected, since the boundary is scoped
  to the Universe page only.

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
- ✅ CONFIRMED (Phase 08 desktop pass) — a consistent, on-brand keyboard-focus indicator
  (`index.css`, `@layer base`) now applies to every link/button/input/select/textarea/
  `role="button"` app-wide. Before this, nothing suppressed the browser's own default
  outline, but nothing styled it either — verified live via real `Tab` key presses (not
  just code reading) that focus now visibly, consistently lands on the correct element in
  document order (back-link → tab bar → page content) on the Overview page, and on Universe
  HUD controls (Reset View confirmed showing the new ring).

## 6. Responsive Behavior

✅ CONFIRMED (Phase 07). Desktop is the primary target. Tablet (768–1279px) gets the
reduced-complexity mid-tier 3D scene by default. Mobile (<768px, `universe/tiers.ts`'s
`MOBILE_WIDTH_BREAKPOINT`) defaults to the 2D List/Table view rather than the 3D Universe,
given the poor fit between orbit controls and small touchscreens — but this is a *default*,
not a lock: a visible "Try 3D Universe" control (`features/universe/UniversePage.tsx`)
switches into the 3D scene on demand whenever WebGL is actually available, and the choice
is only re-applied once per page load (a later resize/rotation never silently overrides an
explicit user choice).

✅ CONFIRMED (Phase 08 desktop pass) — "desktop is the primary target" was true in intent
since Phase 01 but not backed by a desktop-scaling layout until this pass: `WorkspaceLayout`
capped **every** workspace page (including the Universe) at a fixed `max-w-5xl` (1024px)
regardless of monitor size, so a 1440p or 4K display showed the exact same content width as
a 1280px laptop, with the difference spent entirely as unused side margin. Verified live
(real dev servers, real browser, resized through 1280×720, 1366×768, 1440×900, 1920×1080,
2560×1440, and 3840×2160) and fixed:

- The **Universe** (a spatial/canvas workspace, not a reading column) now has no content
  max-width at all — it scales continuously with the viewport, bounded only by padding
  (`px-6 md:px-10 2xl:px-16`). A fixed 1800px cap was tried first and rejected: it still
  looked small and margin-heavy at 2560px/4K in the live check, which is exactly the
  "excessive empty space on large displays" failure mode this pass exists to catch.
- The **2D content pages** (Overview/Quality/Analytics/ML/AI) keep a comfortable, capped
  reading width — `max-w-6xl` (1152px), `max-w-[1400px]` from the `2xl` breakpoint up — a
  deliberate readability choice (a data-quality findings list or an AI narrative paragraph
  gets harder to read, not more useful, stretched edge-to-edge on an ultrawide monitor), not
  an oversight left over from the old fixed cap.
- `AnalyticsPage`'s distribution grid gained an `xl:grid-cols-3` breakpoint (was capped at
  2 columns regardless of available width) so more histograms are visible at once on a wide
  display without individually stretching each one too wide to read.
- Confirmed via `document.documentElement.scrollWidth`/`clientWidth` at 3840×2160: no
  horizontal overflow at any tested size.
- 3D mouse/keyboard interaction was verified live at 1920×1080, not just read from code:
  orbit (drag), zoom (scroll), click-to-select (a real raycast hit on the dataset-core mesh,
  confirmed via its DOM-projected `NodeLabel`'s screen position), hover cursor change,
  Escape-to-close, "Reset View," and search-to-focus (typing a column name, selecting it,
  camera moves to it and opens its real computed feature stats) — all confirmed working
  correctly, not merely present in the DOM.

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

All resolved in Phase 07:

- ✅ RESOLVED — exact color palette: §2, `frontend/tailwind.config.js`, ADR-016.
- ✅ RESOLVED — typography: Inter/JetBrains Mono confirmed (not placeholders), §2.
- ✅ RESOLVED — motion timing/easing: `CameraControls`'s `smoothTime` (0.4s eased, 0s under
  `prefers-reduced-motion`), the idle-float amplitude/speed constants in `universe/
  useFloat.ts`, and the `DetailPanel` slide-in transition (0.22s `easeOut`) — see ADR-016.
- ✅ RESOLVED — performance-tier thresholds: §4.7, `universe/tiers.ts`.
- ✅ RESOLVED — mobile 3D-on-demand interaction: §6.

---
*Related: [PRODUCT_SPEC.md](PRODUCT_SPEC.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[../01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md](../01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md) ·
[../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md](../01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md)*
