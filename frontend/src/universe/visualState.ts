/**
 * Combines a node's structural baseline (`available`/`error`, from `mapping.ts`) with
 * interaction-time state (hover/selection/async loading) into the single visual state
 * every node renders — the concrete state machine from `02_DOCS/UI_UX_SPEC.md` §4.2.
 * Kept separate from `mapping.ts` so the mapping layer stays pure/interaction-free and
 * this precedence logic is independently unit-testable without React or R3F.
 */

import type { NodeVisualState } from "./types";

export interface NodeStateInputs {
  /** Structural: does this node have real, already-computed data behind it? */
  available: boolean;
  /** Structural: is there a genuine data-quality error (e.g. a critical finding)? */
  error?: boolean;
  /** Interaction-time: is an async fetch for this node's own data in flight? */
  loading?: boolean;
  hovered?: boolean;
  selected?: boolean;
}

/** Precedence, highest to lowest: error > loading > disabled > selected > hover > idle. */
export function resolveNodeVisualState(inputs: NodeStateInputs): NodeVisualState {
  if (inputs.error) return "error";
  if (inputs.loading) return "loading";
  if (!inputs.available) return "disabled";
  if (inputs.selected) return "selected";
  if (inputs.hovered) return "hover";
  return "idle";
}
