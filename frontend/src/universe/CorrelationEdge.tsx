import { correlationEdgeColor } from "./sceneTokens";
import { SceneLine } from "./SceneLine";
import type { CorrelationEdge as CorrelationEdgeModel, Vec3 } from "./types";

const MIN_WIDTH = 1;
const MAX_WIDTH = 4;

/** Edge thickness -> normalized |coefficient|; edge color -> sign of the coefficient — the
 * one, documented correlation-edge encoding (§9/§26). Never implies causation (label text
 * everywhere this edge is described says "correlation," never "cause"). */
export function CorrelationEdge({
  edge,
  from,
  to,
  highlighted,
}: {
  edge: CorrelationEdgeModel;
  from: Vec3;
  to: Vec3;
  highlighted: boolean;
}) {
  const magnitude = Math.min(Math.abs(edge.coefficient), 1);
  const lineWidth = MIN_WIDTH + magnitude * (MAX_WIDTH - MIN_WIDTH);
  return (
    <SceneLine
      from={from}
      to={to}
      color={correlationEdgeColor(edge.coefficient)}
      opacity={highlighted ? 0.9 : 0.35 + magnitude * 0.3}
      lineWidth={lineWidth}
    />
  );
}
