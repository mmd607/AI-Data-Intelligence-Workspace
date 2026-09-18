import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Group } from "three";

import { hashString } from "./layout";

const AMPLITUDE = 0.08;
const SPEED = 0.6;

/** Subtle, staggered idle floating motion (§4.2 "small-amplitude, staggered per node so
 * the scene doesn't move in lockstep") — the per-node phase is derived from its id, so it
 * stays deterministic without any extra state. Disabled outright under
 * `prefers-reduced-motion` (§27/§5). */
export function useFloat(nodeId: string, basePositionY: number, reducedMotion: boolean) {
  const ref = useRef<Group>(null);
  const phase = (hashString(nodeId) % 1000) / 1000;

  useFrame(({ clock }) => {
    if (!ref.current) return;
    if (reducedMotion) {
      ref.current.position.y = basePositionY;
      return;
    }
    const t = clock.getElapsedTime();
    ref.current.position.y = basePositionY + Math.sin(t * SPEED + phase * Math.PI * 2) * AMPLITUDE;
  });

  return ref;
}
