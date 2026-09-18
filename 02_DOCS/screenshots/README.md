# Phase 07 — Manual QA / Screenshot Record

`01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md` ("Documentation Requirements") asks for
representative screenshots to be captured here. The agent's browser tooling in this session
renders and inspects the live app (screenshots, the accessibility tree, console/network
logs) but has no primitive to save a captured screenshot as a binary file on disk — only to
view it inline while verifying behavior. Rather than fabricate placeholder images or skip
the requirement silently, this file records exactly what was visually verified, when, and
against what real data, so a human (or a future phase) can reproduce any of these views in
under a minute and capture real PNGs if the repository should carry them.

**Known limitation, recorded per `00_AGENT_CONTROL/DEFINITION_OF_DONE.md`:** no binary
screenshot files are committed by this phase. Everything below was visually confirmed live,
with getpage-text/network/console verification alongside each screenshot, during this
phase's own runtime verification session (see `PHASE_REPORT.md` "Runtime Verification").

## How to reproduce

1. `cd backend && .venv/Scripts/uvicorn app.main:app --port 8000`
2. `cd frontend && npm run dev`
3. Upload any CSV with ≥2 numeric columns (e.g. `backend/tests/fixtures/ml_regression.csv`).
4. Open the dataset's **Universe** tab (first tab in the workspace).

## Views verified

- **Overview** — dataset core (icosahedron) at the center, the 5 domain nodes (Profile,
  Quality, Analytics, ML, AI Insights) orbiting it on dashed connection lines, the AI
  Insights node rendered in the secondary (violet) accent, every other node in the primary
  (cyan) accent, the HUD (Search/Filters/Legend/Reset View/2D-3D toggle) minimal and
  non-obstructive across the top.
- **Analytics domain, focused** — camera eases toward the node; a feature ring of the real
  correlated columns appears with dashed correlation edges between them; the
  `CorrelationPanel` inspector opens on the right showing the exact same pairs/coefficients/
  observation counts as the 3D edges, sorted by strength, with the causation disclaimer.
- **Feature node, selected** (`income`, from the fixture above) — the `FeaturePanel`
  inspector shows real numeric stats (min/max/mean/median/std/IQR), sample values, and an
  "AI column insight" action; clicking it renders a real, grounded offline AI explanation
  with its evidence sources — confirming the computed-vs-AI-generated visual contract
  (`UI_UX_SPEC.md` §4.6) inside the Universe's own panels, not just the pre-existing 2D
  pages.
- **Legend** — a popover documenting every node type, size/color/edge encoding, and state,
  confirmed fully on-screen (a real clipping bug, caused by a `right`-anchored popover
  opening off the left edge of a wrapped HUD row, was found and fixed during this
  verification — see `PHASE_REPORT.md`).
- **2D fallback** (`Switch to 2D`) — the identical dataset/domain/feature/correlation data
  as plain cards, a real `<table>`, and working in-2D selection, confirmed to share
  selection state with the 3D view.
- **Mobile viewport (375×812)** — defaults straight to the 2D fallback with a visible "Try
  3D Universe" affordance, per `UI_UX_SPEC.md` §6.
- **Live cross-tab integration** — trained a real baseline model on the ML tab, then
  navigated in-app (client-side routing, no reload) back to the Universe: the ML domain
  node's availability and the `MLPanel`'s metrics updated to the real just-trained result
  with no page reload, confirming the Universe reads the same session state
  (`state/DatasetSessionContext.tsx`) the rest of the app already uses.
- **Zero console errors** throughout the entire session (confirmed via
  `read_console_messages`) across every interaction above.
