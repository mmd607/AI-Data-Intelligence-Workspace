import type { ThreeEvent } from "@react-three/fiber";

import { NodeLabel } from "./NodeLabel";
import { COLOR, stateColor, STATE_STYLE } from "./sceneTokens";
import type { DomainNode as DomainNodeModel, NodeVisualState } from "./types";
import { useFloat } from "./useFloat";

const AI_DOMAINS = new Set(["ai"]);

export function DomainNode({
  node,
  visualState,
  reducedMotion,
  onSelect,
  onHover,
}: {
  node: DomainNodeModel;
  visualState: NodeVisualState;
  reducedMotion: boolean;
  onSelect: () => void;
  onHover: (hovered: boolean) => void;
}) {
  const style = STATE_STYLE[visualState];
  const groupRef = useFloat(node.id, node.position.y, reducedMotion);
  // The AI domain uses the secondary accent exclusively — every other domain (Profile,
  // Quality, Analytics, ML) is deterministic and shares the primary accent, per the
  // principle-2 color separation documented in `tailwind.config.js`.
  const baseColor = AI_DOMAINS.has(node.domain) ? COLOR.accentSecondary : COLOR.accent;
  const color = stateColor(visualState, baseColor);

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
        <octahedronGeometry args={[0.55, 0]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={style.emissive}
          opacity={style.opacity}
          transparent
        />
      </mesh>
      <NodeLabel
        label={node.label}
        sub={node.summary}
        emphasized={visualState === "selected" || visualState === "hover"}
        muted={visualState === "disabled"}
      />
    </group>
  );
}
