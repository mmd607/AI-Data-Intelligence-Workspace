import { Component, type ReactNode } from "react";

/**
 * Catches render errors thrown anywhere inside the 3D scene tree (a WebGL context loss, a
 * Three.js runtime error, etc.) so a 3D failure never takes down the rest of the
 * application (`01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md` "Error Handling" — "3D
 * failures must NOT destroy the entire application"). Scoped to `UniversePage` only, not
 * the app root, so every other tab keeps working regardless.
 */
export class UniverseErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // eslint-disable-next-line no-console -- deliberate: a 3D failure is worth surfacing to devtools, not silencing.
    console.error("3D Universe scene failed to render:", error);
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}
