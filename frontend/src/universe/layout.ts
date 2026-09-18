/**
 * Deterministic spatial layout — the same dataset (and the same domain/column ordering)
 * always produces the same positions, per `02_DOCS/UI_UX_SPEC.md` §10's "avoid random
 * positions on every render; if randomness is required for aesthetics, use a deterministic
 * seed." No `Math.random()` is used anywhere in this file.
 *
 * - The dataset core sits at the origin; the 5 domain nodes sit on a fixed ring around it
 *   (their order/angles never depend on data, so no seed is needed there).
 * - Each domain's feature ring uses a golden-angle "sunflower" spiral (even, non-
 *   overlapping spacing) rotated by a per-dataset deterministic offset, so different
 *   datasets look visually distinct while the same dataset is always stable.
 */

import type { DomainKey, Vec3 } from "./types";

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

export const DOMAIN_ORDER: DomainKey[] = ["profile", "quality", "analytics", "ml", "ai"];

const DOMAIN_RADIUS = 6;
const FEATURE_RADIUS = 3;

/** FNV-1a 32-bit — small, dependency-free, deterministic string hash. */
export function hashString(input: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** mulberry32 — a small, deterministic PRNG step; not used for anything security-sensitive. */
export function seededRandom01(seed: number): number {
  let t = (seed + 0x6d2b79f5) >>> 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

export function datasetCorePosition(): Vec3 {
  return { x: 0, y: 0, z: 0 };
}

export function domainNodePosition(domain: DomainKey): Vec3 {
  const index = DOMAIN_ORDER.indexOf(domain);
  const angle = (index / DOMAIN_ORDER.length) * Math.PI * 2;
  return {
    x: Math.cos(angle) * DOMAIN_RADIUS,
    y: Math.sin(index * 1.3) * 0.6,
    z: Math.sin(angle) * DOMAIN_RADIUS,
  };
}

/** Golden-angle ring positions around a domain node, rotated by a per-dataset seed. */
export function featureRingPositions(
  datasetId: string,
  domain: Extract<DomainKey, "profile" | "analytics">,
  count: number,
): Vec3[] {
  if (count <= 0) return [];
  const center = domainNodePosition(domain);
  const startAngle = seededRandom01(hashString(`${datasetId}:${domain}`)) * Math.PI * 2;

  const positions: Vec3[] = [];
  for (let i = 0; i < count; i++) {
    const angle = startAngle + i * GOLDEN_ANGLE;
    const radius = FEATURE_RADIUS * Math.sqrt((i + 0.5) / count);
    positions.push({
      x: center.x + Math.cos(angle) * radius,
      y: center.y + ((i % 5) - 2) * 0.15,
      z: center.z + Math.sin(angle) * radius,
    });
  }
  return positions;
}
