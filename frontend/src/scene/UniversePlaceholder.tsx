/**
 * Proves the React Three Fiber render pipeline works end-to-end.
 *
 * This is explicitly NOT the "Data Intelligence Universe" (that is Phase 07's scope, per
 * 01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md and 02_DOCS/UI_UX_SPEC.md §4). Per
 * PHASE_01_FOUNDATION's own "UI requirement" ("do not spend the phase building the final
 * 3D universe"), this component is a minimal, honestly-labeled placeholder — a single
 * slowly rotating wireframe form, nothing that resembles finished node/connection content,
 * so nobody mistakes it for real Universe UI.
 */

import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh } from "three";

function SpinningPlaceholder() {
  const meshRef = useRef<Mesh>(null);

  useFrame((_state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.15;
      meshRef.current.rotation.y += delta * 0.2;
    }
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.2, 0]} />
      <meshBasicMaterial color="#6ee7ff" wireframe />
    </mesh>
  );
}

export function UniversePlaceholder() {
  return (
    <div className="h-64 w-full overflow-hidden rounded-lg border border-white/10 bg-surface-raised">
      <Canvas camera={{ position: [0, 0, 4] }}>
        <ambientLight intensity={0.6} />
        <SpinningPlaceholder />
        <OrbitControls enableZoom={false} autoRotate={false} />
      </Canvas>
    </div>
  );
}
