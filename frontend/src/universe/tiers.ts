/**
 * Performance-tier detection and `prefers-reduced-motion` — closes the two remaining
 * `02_DOCS/UI_UX_SPEC.md` §9 open questions ("exact performance-tier thresholds",
 * "mobile 3D-on-demand interaction details") with concrete, testable logic. See
 * `02_DOCS/decisions/DECISIONS_LOG.md` ADR-016 for the reasoning behind the exact numbers.
 */

import { useEffect, useState } from "react";

export type PerformanceTier = "high" | "mid" | "low";

export interface TierResult {
  tier: PerformanceTier;
  webglAvailable: boolean;
  /** True when the Canvas should not mount at all — the 2D fallback is the only view. */
  forceFallback: boolean;
  /** The feature-node cap this tier allows (large-dataset handling, phase brief §11). */
  featureNodeCap: number;
}

const HIGH_FEATURE_CAP = 60;
const MID_FEATURE_CAP = 30;

const MOBILE_WIDTH_BREAKPOINT = 768;
const DESKTOP_WIDTH_BREAKPOINT = 1280;
const LOW_HARDWARE_CONCURRENCY = 4;

/** A throwaway canvas WebGL probe — never touches the real scene canvas. */
export function probeWebGLAvailable(doc: Document = document): boolean {
  try {
    const canvas = doc.createElement("canvas");
    const gl = canvas.getContext("webgl") ?? canvas.getContext("experimental-webgl");
    return !!gl;
  } catch {
    return false;
  }
}

export interface DetectTierOptions {
  windowWidth?: number;
  hardwareConcurrency?: number;
  webglAvailable?: boolean;
}

export function detectPerformanceTier(opts: DetectTierOptions = {}): TierResult {
  const windowWidth = opts.windowWidth ?? (typeof window !== "undefined" ? window.innerWidth : DESKTOP_WIDTH_BREAKPOINT);
  const hardwareConcurrency =
    opts.hardwareConcurrency ?? (typeof navigator !== "undefined" ? navigator.hardwareConcurrency : undefined);
  const webglAvailable = opts.webglAvailable ?? (typeof document !== "undefined" ? probeWebGLAvailable() : false);

  if (!webglAvailable) {
    return { tier: "low", webglAvailable: false, forceFallback: true, featureNodeCap: MID_FEATURE_CAP };
  }
  // Mobile defaults to the 2D fallback (UI_UX_SPEC.md §6) — 3D remains reachable on-demand
  // via the view-mode toggle, which is a UniversePage/store concern, not this function's.
  if (windowWidth < MOBILE_WIDTH_BREAKPOINT) {
    return { tier: "low", webglAvailable: true, forceFallback: true, featureNodeCap: MID_FEATURE_CAP };
  }
  if (windowWidth < DESKTOP_WIDTH_BREAKPOINT || (hardwareConcurrency !== undefined && hardwareConcurrency <= LOW_HARDWARE_CONCURRENCY)) {
    return { tier: "mid", webglAvailable: true, forceFallback: false, featureNodeCap: MID_FEATURE_CAP };
  }
  return { tier: "high", webglAvailable: true, forceFallback: false, featureNodeCap: HIGH_FEATURE_CAP };
}

function readReducedMotionPreference(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Respects `prefers-reduced-motion` (§27/§5) — floating/pulse/camera-ease animations are
 * removed or snapped instantly wherever this returns `true`. */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(readReducedMotionPreference);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mql.addEventListener?.("change", handler);
    return () => mql.removeEventListener?.("change", handler);
  }, []);

  return reduced;
}
