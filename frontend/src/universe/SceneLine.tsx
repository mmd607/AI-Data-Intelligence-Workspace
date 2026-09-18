import { Line } from "@react-three/drei";

import type { Vec3 } from "./types";

/** A thin shared line primitive for both domain-connection lines and correlation edges —
 * dashed to read as "a relationship," not static wireframe geometry (§4.3). Deliberately
 * static (no per-frame dash-offset animation): the phase's own "Performance" requirement
 * ("avoid ... expensive effects") outweighs a purely decorative animated flow here — the
 * hover/selection highlight already communicates "alive." */
export function SceneLine({
  from,
  to,
  color,
  opacity,
  lineWidth,
}: {
  from: Vec3;
  to: Vec3;
  color: string;
  opacity: number;
  lineWidth: number;
}) {
  return (
    <Line
      points={[
        [from.x, from.y, from.z],
        [to.x, to.y, to.z],
      ]}
      color={color}
      lineWidth={lineWidth}
      transparent
      opacity={opacity}
      dashed
      dashSize={0.18}
      gapSize={0.12}
    />
  );
}
