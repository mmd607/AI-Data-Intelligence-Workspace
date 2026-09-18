import { CameraControls, Stars } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";

import { useUniverseStore } from "../state/universeStore";
import { CorrelationEdge } from "./CorrelationEdge";
import { DatasetCoreNode } from "./DatasetCoreNode";
import { DomainNode } from "./DomainNode";
import { FeatureNode } from "./FeatureNode";
import { filterFeatureNodes } from "./filtering";
import { SceneLine } from "./SceneLine";
import { COLOR } from "./sceneTokens";
import type { PerformanceTier } from "./tiers";
import type { UniverseGraph, Vec3 } from "./types";
import { resolveNodeVisualState } from "./visualState";

const OVERVIEW_POSITION: Vec3 = { x: 0, y: 9, z: 17 };
const OVERVIEW_TARGET: Vec3 = { x: 0, y: 0, z: 0 };
const FOCUS_DISTANCE = 4.5;

function vectorLength(v: Vec3): number {
  return Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
}

function focusCameraPosition(target: Vec3): Vec3 {
  const length = vectorLength(target);
  const direction = length > 0.001 ? { x: target.x / length, y: 0.35, z: target.z / length } : { x: 0.3, y: 0.5, z: 1 };
  return {
    x: target.x + direction.x * FOCUS_DISTANCE,
    y: target.y + direction.y * FOCUS_DISTANCE,
    z: target.z + direction.z * FOCUS_DISTANCE,
  };
}

function nodePositionMap(graph: UniverseGraph): Map<string, Vec3> {
  const map = new Map<string, Vec3>();
  map.set(graph.datasetNode.id, graph.datasetNode.position);
  for (const d of graph.domainNodes) map.set(d.id, d.position);
  for (const f of graph.featureNodesByDomain.profile) map.set(f.id, f.position);
  for (const f of graph.featureNodesByDomain.analytics) map.set(f.id, f.position);
  return map;
}

function CameraRig({ graph, reducedMotion }: { graph: UniverseGraph; reducedMotion: boolean }) {
  const controlsRef = useRef<CameraControls>(null);
  const focusedNodeId = useUniverseStore((s) => s.focusedNodeId);
  const positions = useMemo(() => nodePositionMap(graph), [graph]);

  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls) return;
    const enableTransition = !reducedMotion;

    const target = focusedNodeId ? positions.get(focusedNodeId) : null;
    if (target) {
      const camera = focusCameraPosition(target);
      void controls.setLookAt(camera.x, camera.y, camera.z, target.x, target.y, target.z, enableTransition);
    } else {
      void controls.setLookAt(
        OVERVIEW_POSITION.x,
        OVERVIEW_POSITION.y,
        OVERVIEW_POSITION.z,
        OVERVIEW_TARGET.x,
        OVERVIEW_TARGET.y,
        OVERVIEW_TARGET.z,
        enableTransition,
      );
    }
  }, [focusedNodeId, positions, reducedMotion]);

  return (
    <CameraControls
      ref={controlsRef}
      minDistance={3}
      maxDistance={30}
      dollySpeed={0.6}
      smoothTime={reducedMotion ? 0 : 0.4}
    />
  );
}

export function UniverseScene({ graph, tier, reducedMotion }: { graph: UniverseGraph; tier: PerformanceTier; reducedMotion: boolean }) {
  const selectedNodeId = useUniverseStore((s) => s.selectedNodeId);
  const hoveredNodeId = useUniverseStore((s) => s.hoveredNodeId);
  const focusedNodeId = useUniverseStore((s) => s.focusedNodeId);
  const filters = useUniverseStore((s) => s.filters);
  const searchQuery = useUniverseStore((s) => s.searchQuery);
  const selectNode = useUniverseStore((s) => s.selectNode);
  const focusNode = useUniverseStore((s) => s.focusNode);
  const hoverNode = useUniverseStore((s) => s.hoverNode);

  const activeRing = focusedNodeId ?? selectedNodeId;
  const profileRingVisible =
    activeRing === "domain:profile" || Boolean(activeRing?.startsWith("feature:profile:")) || searchQuery.trim() !== "" ||
    Object.values(filters).some(Boolean);
  const analyticsRingVisible = activeRing === "domain:analytics" || Boolean(activeRing?.startsWith("feature:analytics:"));

  const correlatedColumns = useMemo(
    () => new Set(graph.featureNodesByDomain.analytics.map((n) => n.column)),
    [graph.featureNodesByDomain.analytics],
  );

  const visibleProfileFeatures = useMemo(() => {
    if (!profileRingVisible) return [];
    return filterFeatureNodes(graph.featureNodesByDomain.profile, filters, searchQuery, {
      correlatedColumns,
      mlColumns: new Set(),
    });
  }, [profileRingVisible, graph.featureNodesByDomain.profile, filters, searchQuery, correlatedColumns]);

  const edgeHighlightColumns = useMemo(() => {
    if (!hoveredNodeId && !selectedNodeId) return null;
    const active = hoveredNodeId ?? selectedNodeId;
    return active;
  }, [hoveredNodeId, selectedNodeId]);

  const positions = useMemo(() => nodePositionMap(graph), [graph]);

  return (
    <div className="h-full w-full">
      <Canvas camera={{ position: [OVERVIEW_POSITION.x, OVERVIEW_POSITION.y, OVERVIEW_POSITION.z], fov: 50 }}>
        <color attach="background" args={["#0a0b0f"]} />
        {tier === "high" && <fog attach="fog" args={["#0a0b0f", 18, 36]} />}
        <ambientLight intensity={0.55} />
        <pointLight position={[8, 10, 8]} intensity={0.6} color={COLOR.accent} />
        <pointLight position={[-8, -6, -8]} intensity={0.3} color={COLOR.accentSecondary} />
        {tier === "high" && !reducedMotion && <Stars radius={60} depth={30} count={1200} factor={2} saturation={0} fade speed={0.3} />}

        <CameraRig graph={graph} reducedMotion={reducedMotion} />

        {graph.domainConnections.map((conn) => {
          const from = positions.get(conn.source);
          const to = positions.get(conn.target);
          if (!from || !to) return null;
          const domainNode = graph.domainNodes.find((d) => d.id === conn.target);
          const highlighted = conn.target === hoveredNodeId || conn.target === selectedNodeId;
          return (
            <SceneLine
              key={conn.id}
              from={from}
              to={to}
              color={domainNode?.available ? COLOR.accent : COLOR.neutralDim}
              opacity={highlighted ? 0.8 : 0.25}
              lineWidth={highlighted ? 2 : 1}
            />
          );
        })}

        {analyticsRingVisible &&
          graph.correlationEdges.map((edge) => {
            const from = positions.get(edge.source);
            const to = positions.get(edge.target);
            if (!from || !to) return null;
            const highlighted = edge.source === edgeHighlightColumns || edge.target === edgeHighlightColumns;
            return <CorrelationEdge key={edge.id} edge={edge} from={from} to={to} highlighted={highlighted} />;
          })}

        <DatasetCoreNode
          node={graph.datasetNode}
          visualState={resolveNodeVisualState({
            available: true,
            hovered: hoveredNodeId === graph.datasetNode.id,
            selected: selectedNodeId === graph.datasetNode.id,
          })}
          reducedMotion={reducedMotion}
          onSelect={() => focusNode(graph.datasetNode.id)}
          onHover={(hovered) => hoverNode(hovered ? graph.datasetNode.id : null)}
        />

        {graph.domainNodes.map((domain) => (
          <DomainNode
            key={domain.id}
            node={domain}
            visualState={resolveNodeVisualState({
              available: domain.available,
              hovered: hoveredNodeId === domain.id,
              selected: selectedNodeId === domain.id,
            })}
            reducedMotion={reducedMotion}
            onSelect={() => focusNode(domain.id)}
            onHover={(hovered) => hoverNode(hovered ? domain.id : null)}
          />
        ))}

        {visibleProfileFeatures.map((feature) => (
          <FeatureNode
            key={feature.id}
            node={feature}
            visualState={resolveNodeVisualState({
              available: true,
              error: feature.hasQualityCritical,
              hovered: hoveredNodeId === feature.id,
              selected: selectedNodeId === feature.id,
            })}
            reducedMotion={reducedMotion}
            onSelect={() => selectNode(feature.id)}
            onHover={(hovered) => hoverNode(hovered ? feature.id : null)}
          />
        ))}

        {analyticsRingVisible &&
          graph.featureNodesByDomain.analytics.map((feature) => (
            <FeatureNode
              key={feature.id}
              node={feature}
              visualState={resolveNodeVisualState({
                available: true,
                error: feature.hasQualityCritical,
                hovered: hoveredNodeId === feature.id,
                selected: selectedNodeId === feature.id,
              })}
              reducedMotion={reducedMotion}
              onSelect={() => selectNode(feature.id)}
              onHover={(hovered) => hoverNode(hovered ? feature.id : null)}
            />
          ))}
      </Canvas>
    </div>
  );
}
