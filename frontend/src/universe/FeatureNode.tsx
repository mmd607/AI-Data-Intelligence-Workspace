import type { ThreeEvent } from "@react-three/fiber";

import { NodeLabel } from "./NodeLabel";
import { SEMANTIC_TYPE_COLOR, stateColor, STATE_STYLE } from "./sceneTokens";
import type { FeatureNode as FeatureNodeModel, NodeVisualState } from "./types";
import { useFloat } from "./useFloat";

const MIN_RADIUS = 0.14;
const MAX_RADIUS = 0.34;

/** Size encoding — the single, documented meaning of feature-node size: normalized
 * missingness (`02_DOCS/decisions/DECISIONS_LOG.md` ADR-016). A 0%-missing column renders
 * at the minimum radius; a 100%-missing column renders at the maximum. */
function radiusForNullPercentage(nullPercentage: number): number {
  const normalized = Math.min(Math.max(nullPercentage, 0), 100) / 100;
  return MIN_RADIUS + normalized * (MAX_RADIUS - MIN_RADIUS);
}

export function FeatureNode({
  node,
  visualState,
  reducedMotion,
  onSelect,
  onHover,
}: {
  node: FeatureNodeModel;
  visualState: NodeVisualState;
  reducedMotion: boolean;
  onSelect: () => void;
  onHover: (hovered: boolean) => void;
}) {
  const style = STATE_STYLE[visualState];
  const groupRef = useFloat(node.id, node.position.y, reducedMotion);
  const baseColor = SEMANTIC_TYPE_COLOR[node.semanticType];
  const color = stateColor(visualState, baseColor);
  const radius = radiusForNullPercentage(node.nullPercentage);

  function handlePointerOver(e: ThreeEvent<PointerEvent>) {
    e.stopPropagation();
    onHover(true);
    document.body.style.cursor = "pointer";
  }
  function handlePointerOut(e: ThreeEvent<PointerEvent>) {
    e.stopPropagation();
    onHover(false);
    document.body.style.cursor = "auto";
  }
  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation();
    onSelect();
  }

  return (
    <group ref={groupRef} position={[node.position.x, node.position.y, node.position.z]}>
      <mesh
        scale={style.scale}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      >
        <sphereGeometry args={[radius, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={style.emissive}
          opacity={style.opacity}
          transparent
        />
      </mesh>
      {(visualState === "hover" || visualState === "selected") && (
        <NodeLabel
          label={node.column}
          sub={`${node.semanticType} · ${node.nullPercentage}% missing`}
          emphasized
        />
      )}
    </group>
  );
}
