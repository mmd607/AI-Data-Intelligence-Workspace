/**
 * Domain model for the "Data Intelligence Universe" scene — the output of the mapping
 * layer (`mapping.ts`), consumed by both the R3F scene and the 2D fallback. Nothing in
 * this file knows about Three.js/R3F; it is plain data, per
 * `02_DOCS/ARCHITECTURE.md` "Module Boundaries" ("The 3D scene should receive clean
 * domain objects").
 */

import type { SemanticType } from "../api-client";

export type NodeType = "dataset" | "domain" | "feature";

/** The 5 fixed domain nodes orbiting the dataset core (`02_DOCS/UI_UX_SPEC.md` §4.1,
 * with "Statistics"/"Visualization" merged into "Analytics" — see
 * `02_DOCS/decisions/DECISIONS_LOG.md` ADR-016 for why). */
export type DomainKey = "profile" | "quality" | "analytics" | "ml" | "ai";

/** The node state machine, `02_DOCS/UI_UX_SPEC.md` §4.2 — the minimum state set every
 * node must implement. `resolveNodeVisualState` (`visualState.ts`) computes this from
 * structural availability (this file) plus interaction-time state (hover/selection/async
 * status), kept separate so this mapping layer stays pure and interaction-free. */
export type NodeVisualState = "idle" | "hover" | "selected" | "loading" | "error" | "disabled";

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

interface BaseNode {
  id: string;
  type: NodeType;
  label: string;
  position: Vec3;
  /** The structural baseline state (`idle` | `disabled` | `error`) — see `visualState.ts`
   * for how this combines with hover/selection/loading at render time. */
  state: NodeVisualState;
}

export interface DatasetCoreNode extends BaseNode {
  type: "dataset";
  rowCount: number;
  columnCount: number;
}

export interface DomainNode extends BaseNode {
  type: "domain";
  domain: DomainKey;
  /** Whether this domain has real, already-computed data behind it right now. */
  available: boolean;
  /** A short, real-data-derived summary line (never fabricated) shown on hover/label. */
  summary: string;
}

export interface FeatureNode extends BaseNode {
  type: "feature";
  /** Which ring this feature instance belongs to — a column may appear as two separate
   * node instances (profile ring and analytics ring) with independent positions. */
  domain: Extract<DomainKey, "profile" | "analytics">;
  column: string;
  semanticType: SemanticType;
  /** Size encoding — the single, documented meaning of feature-node size
   * (`02_DOCS/UI_UX_SPEC.md` §7/ADR-016): normalized missingness. */
  nullPercentage: number;
  hasQualityWarning: boolean;
  hasQualityCritical: boolean;
}

export type UniverseNode = DatasetCoreNode | DomainNode | FeatureNode;

/** A real correlation pair, never a fabricated relationship (product principle 6). */
export interface CorrelationEdge {
  id: string;
  source: string;
  target: string;
  coefficient: number;
  observations: number;
}

/** The always-present dataset→domain connection lines (§4.3). */
export interface DomainConnection {
  id: string;
  source: string;
  target: string;
}

export interface UniverseGraph {
  datasetNode: DatasetCoreNode;
  domainNodes: DomainNode[];
  featureNodesByDomain: Record<Extract<DomainKey, "profile" | "analytics">, FeatureNode[]>;
  correlationEdges: CorrelationEdge[];
  domainConnections: DomainConnection[];
}
