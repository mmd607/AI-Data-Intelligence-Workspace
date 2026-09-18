/**
 * The domain → spatial mapping layer (`02_DOCS/ARCHITECTURE.md` "Module Boundaries" /
 * `01_PHASES/PHASE_07_3D_UNIVERSE_UI/PHASE_PROMPT.md` "Files/Components Expected"):
 * transforms already-fetched, real backend responses into a `UniverseGraph`. Pure and
 * synchronous — no `fetch`, no Three.js, no randomness beyond `layout.ts`'s deterministic
 * seeding. Every field on every returned node traces to a real API value; nothing here
 * invents a statistic, a relationship, or a quality score (product principle 1/6).
 */

import type {
  AIStatusResponse,
  CorrelationResult,
  DatasetMetadata,
  DatasetProfile,
  ModelResult,
  QualitySeverity,
  QualitySummary,
} from "../api-client";
import { datasetCorePosition, DOMAIN_ORDER, domainNodePosition, featureRingPositions } from "./layout";
import type { CorrelationEdge, DatasetCoreNode, DomainConnection, DomainKey, DomainNode, FeatureNode, UniverseGraph } from "./types";

/** All columns up to this cap populate the Profile feature ring — the rest remain fully
 * accessible via the 2D fallback's search/table, never silently dropped. */
export const PROFILE_FEATURE_CAP = 60;
/** Only the strongest N correlation pairs (by |coefficient|) become edges/analytics
 * feature nodes — the large-dataset strategy from the phase brief §11, not a fabricated
 * "no relationship" for the rest. */
export const ANALYTICS_PAIR_CAP = 30;

const DOMAIN_LABELS: Record<DomainKey, string> = {
  profile: "Data Profile",
  quality: "Data Quality",
  analytics: "Analytics",
  ml: "ML",
  ai: "AI Insights",
};

export interface BuildUniverseGraphInput {
  dataset: DatasetMetadata;
  profile: DatasetProfile | null;
  quality: QualitySummary | null;
  correlation: CorrelationResult | null;
  mlResult: ModelResult | null;
  aiStatus: AIStatusResponse | null;
}

function columnHasFinding(quality: QualitySummary | null, column: string, severities: QualitySeverity[]): boolean {
  if (!quality) return false;
  return quality.findings.some((f) => f.column === column && severities.includes(f.severity));
}

function domainAvailability(domain: DomainKey, input: BuildUniverseGraphInput): { available: boolean; summary: string } {
  switch (domain) {
    case "profile":
      return input.profile
        ? { available: true, summary: `${input.profile.column_count} columns profiled` }
        : { available: false, summary: "Not loaded yet" };
    case "quality":
      return input.quality
        ? {
            available: true,
            summary: `${input.quality.finding_count} finding${input.quality.finding_count === 1 ? "" : "s"}`,
          }
        : { available: false, summary: "Not loaded yet" };
    case "analytics":
      if (!input.correlation) return { available: false, summary: "Not loaded yet" };
      return input.correlation.status === "computed"
        ? {
            available: true,
            summary: `${input.correlation.pairs.length} correlation pair${input.correlation.pairs.length === 1 ? "" : "s"}`,
          }
        : { available: true, summary: input.correlation.message ?? "Insufficient data for correlation" };
    case "ml":
      return input.mlResult
        ? { available: true, summary: `${input.mlResult.model_name} · ${input.mlResult.task_type}` }
        : { available: false, summary: "No model trained yet" };
    case "ai":
      if (!input.aiStatus) return { available: false, summary: "Not loaded yet" };
      return input.aiStatus.available
        ? { available: true, summary: `${input.aiStatus.provider} available` }
        : { available: false, summary: input.aiStatus.reason ?? "AI unavailable" };
  }
}

function buildDomainNodes(input: BuildUniverseGraphInput): DomainNode[] {
  return DOMAIN_ORDER.map((domain) => {
    const { available, summary } = domainAvailability(domain, input);
    return {
      id: `domain:${domain}`,
      type: "domain",
      domain,
      label: DOMAIN_LABELS[domain],
      position: domainNodePosition(domain),
      state: available ? "idle" : "disabled",
      available,
      summary,
    };
  });
}

function buildProfileFeatureNodes(input: BuildUniverseGraphInput): FeatureNode[] {
  if (!input.profile) return [];
  const columns = input.profile.columns.slice(0, PROFILE_FEATURE_CAP);
  const positions = featureRingPositions(input.dataset.id, "profile", columns.length);
  return columns.map((col, i) => {
    const hasCritical = columnHasFinding(input.quality, col.name, ["critical"]);
    const hasWarning = columnHasFinding(input.quality, col.name, ["warning"]);
    return {
      id: `feature:profile:${col.name}`,
      type: "feature",
      domain: "profile",
      column: col.name,
      label: col.name,
      position: positions[i],
      state: hasCritical ? "error" : "idle",
      semanticType: col.semantic_type,
      nullPercentage: col.null_percentage,
      hasQualityWarning: hasWarning,
      hasQualityCritical: hasCritical,
    };
  });
}

function buildAnalyticsRing(input: BuildUniverseGraphInput): { featureNodes: FeatureNode[]; edges: CorrelationEdge[] } {
  if (!input.correlation || input.correlation.status !== "computed" || !input.profile) {
    return { featureNodes: [], edges: [] };
  }

  const topPairs = [...input.correlation.pairs]
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, ANALYTICS_PAIR_CAP);

  const touchedColumns: string[] = [];
  const seen = new Set<string>();
  for (const pair of topPairs) {
    if (!seen.has(pair.column_a)) {
      seen.add(pair.column_a);
      touchedColumns.push(pair.column_a);
    }
    if (!seen.has(pair.column_b)) {
      seen.add(pair.column_b);
      touchedColumns.push(pair.column_b);
    }
  }

  const profileByName = new Map(input.profile.columns.map((c) => [c.name, c]));
  const positions = featureRingPositions(input.dataset.id, "analytics", touchedColumns.length);
  const featureNodes: FeatureNode[] = touchedColumns.map((name, i) => {
    const col = profileByName.get(name);
    const hasCritical = columnHasFinding(input.quality, name, ["critical"]);
    const hasWarning = columnHasFinding(input.quality, name, ["warning"]);
    return {
      id: `feature:analytics:${name}`,
      type: "feature",
      domain: "analytics",
      column: name,
      label: name,
      position: positions[i],
      state: hasCritical ? "error" : "idle",
      semanticType: col?.semantic_type ?? "unknown",
      nullPercentage: col?.null_percentage ?? 0,
      hasQualityWarning: hasWarning,
      hasQualityCritical: hasCritical,
    };
  });

  const edges: CorrelationEdge[] = topPairs.map((pair) => ({
    id: `edge:${pair.column_a}::${pair.column_b}`,
    source: `feature:analytics:${pair.column_a}`,
    target: `feature:analytics:${pair.column_b}`,
    coefficient: pair.coefficient,
    observations: pair.observations,
  }));

  return { featureNodes, edges };
}

export function buildUniverseGraph(input: BuildUniverseGraphInput): UniverseGraph {
  const datasetNode: DatasetCoreNode = {
    id: "dataset",
    type: "dataset",
    label: input.dataset.original_filename,
    position: datasetCorePosition(),
    state: "idle",
    rowCount: input.dataset.row_count,
    columnCount: input.dataset.column_count,
  };

  const domainNodes = buildDomainNodes(input);
  const domainConnections: DomainConnection[] = domainNodes.map((d) => ({
    id: `connection:dataset->${d.id}`,
    source: "dataset",
    target: d.id,
  }));

  const profileFeatureNodes = buildProfileFeatureNodes(input);
  const { featureNodes: analyticsFeatureNodes, edges: correlationEdges } = buildAnalyticsRing(input);

  return {
    datasetNode,
    domainNodes,
    featureNodesByDomain: { profile: profileFeatureNodes, analytics: analyticsFeatureNodes },
    correlationEdges,
    domainConnections,
  };
}
