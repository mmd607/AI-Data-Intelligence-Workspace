import type { ThreeEvent } from "@react-three/fiber";

import type { DatasetCoreNode as DatasetCoreNodeModel } from "./types";
import { NodeLabel } from "./NodeLabel";
import { COLOR, STATE_STYLE } from "./sceneTokens";
import { useFloat } from "./useFloat";
import type { NodeVisualState } from "./types";

export function DatasetCoreNode({
  node,
  visualState,
  reducedMotion,
  onSelect,
  onHover,
}: {
  node: DatasetCoreNodeModel;
  visualState: NodeVisualState;
  reducedMotion: boolean;
  onSelect: () => void;
  onHover: (hovered: boolean) => void;
}) {
  const style = STATE_STYLE[visualState];
  const groupRef = useFloat(node.id, node.position.y, reducedMotion);

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
        <icosahedronGeometry args={[1.1, 1]} />
        <meshStandardMaterial
          color={COLOR.accent}
          emissive={COLOR.accent}
          emissiveIntensity={style.emissive}
          opacity={style.opacity}
          transparent
          wireframe={visualState === "disabled"}
        />
      </mesh>
      <NodeLabel
        label={node.label}
        sub={`${node.rowCount.toLocaleString()} rows · ${node.columnCount} columns`}
        emphasized={visualState === "selected" || visualState === "hover"}
      />
    </group>
  );
}
