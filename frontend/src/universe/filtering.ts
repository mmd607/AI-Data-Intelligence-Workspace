/**
 * Pure filter/search logic over feature nodes — separated from rendering so `Search.tsx`/
 * `Filters.tsx`/`UniverseScene.tsx` all narrow the same feature set consistently, and so
 * this logic is unit-testable without mounting the 3D scene (`TESTING_STRATEGY.md` §4).
 */

import type { UniverseFilters } from "../state/universeStore";
import type { FeatureNode } from "./types";

export interface FilterContext {
  /** Columns touched by a real correlation edge (derived from the analytics ring). */
  correlatedColumns: ReadonlySet<string>;
  /** Columns that are the target or a feature of the last-trained `ModelResult`. */
  mlColumns: ReadonlySet<string>;
}

export function hasActiveFilters(filters: UniverseFilters): boolean {
  return Object.values(filters).some(Boolean);
}

function matchesActiveFilters(node: FeatureNode, filters: UniverseFilters, ctx: FilterContext): boolean {
  const active: boolean[] = [];
  if (filters.numeric) active.push(node.semanticType === "numeric");
  if (filters.categorical) active.push(node.semanticType === "categorical");
  if (filters.missing) active.push(node.nullPercentage > 0);
  if (filters.qualityWarning) active.push(node.hasQualityWarning || node.hasQualityCritical);
  if (filters.correlated) active.push(ctx.correlatedColumns.has(node.column));
  if (filters.mlRelated) active.push(ctx.mlColumns.has(node.column));
  // No filter selected -> nothing to narrow by, everything matches.
  if (active.length === 0) return true;
  // Selected filters combine as OR ("any of these categories") — simpler and more
  // forgiving than AND for a small, opt-in filter chip set (chat brief §24).
  return active.some(Boolean);
}

export function filterFeatureNodes(
  nodes: FeatureNode[],
  filters: UniverseFilters,
  searchQuery: string,
  ctx: FilterContext,
): FeatureNode[] {
  const query = searchQuery.trim().toLowerCase();
  return nodes.filter((node) => {
    if (query && !node.column.toLowerCase().includes(query)) return false;
    return matchesActiveFilters(node, filters, ctx);
  });
}
