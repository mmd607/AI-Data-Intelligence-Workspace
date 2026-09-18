/**
 * The 3D scene's material colors — Three.js materials need real hex values, not Tailwind
 * classes, so this file is the single source of truth mirroring `tailwind.config.js`'s 2D
 * tokens. Keeping them in one place is what "visual encoding must be documented and
 * consistent" (`02_DOCS/UI_UX_SPEC.md` §26) means in practice for the 3D layer.
 */

import type { SemanticType } from "../api-client";
import type { NodeVisualState } from "./types";

export const COLOR = {
  accent: "#6ee7ff",
  accentSecondary: "#a78bfa",
  neutral: "#94a3b8",
  neutralDim: "#475569",
  warning: "#f59e0b",
  critical: "#f43f5e",
} as const;

/** Feature-node color → `semantic_type` (the one, documented color mapping — §7/§26). */
export const SEMANTIC_TYPE_COLOR: Record<SemanticType, string> = {
  numeric: COLOR.accent,
  categorical: COLOR.accentSecondary,
  boolean: "#38bdf8",
  datetime: "#34d399",
  text: COLOR.neutral,
  unknown: COLOR.neutralDim,
};

/** Correlation-edge color → sign of the coefficient (§9/§26) — never a heatmap gradient. */
export function correlationEdgeColor(coefficient: number): string {
  return coefficient >= 0 ? "#38bdf8" : "#fb7185";
}

/** Per-visual-state emissive intensity / opacity — a single shared table so every node
 * type renders the same state consistently (§4.2). */
export const STATE_STYLE: Record<NodeVisualState, { emissive: number; opacity: number; scale: number }> = {
  idle: { emissive: 0.35, opacity: 0.95, scale: 1 },
  hover: { emissive: 0.65, opacity: 1, scale: 1.12 },
  selected: { emissive: 0.9, opacity: 1, scale: 1.18 },
  loading: { emissive: 0.5, opacity: 0.85, scale: 1 },
  error: { emissive: 0.55, opacity: 1, scale: 1 },
  disabled: { emissive: 0.08, opacity: 0.35, scale: 0.85 },
};

export function stateColor(state: NodeVisualState, baseColor: string): string {
  if (state === "error") return COLOR.critical;
  if (state === "loading") return COLOR.warning;
  return baseColor;
}
