import { describe, expect, it } from "vitest";

import { DEFAULT_FILTERS } from "../state/universeStore";
import { filterFeatureNodes, hasActiveFilters } from "./filtering";
import type { FeatureNode } from "./types";

function makeFeature(overrides: Partial<FeatureNode> = {}): FeatureNode {
  return {
    id: `feature:profile:${overrides.column ?? "col"}`,
    type: "feature",
    domain: "profile",
    column: "col",
    label: "col",
    position: { x: 0, y: 0, z: 0 },
    state: "idle",
    semanticType: "numeric",
    nullPercentage: 0,
    hasQualityWarning: false,
    hasQualityCritical: false,
    ...overrides,
  };
}

const nodes: FeatureNode[] = [
  makeFeature({ column: "age", semanticType: "numeric", nullPercentage: 0 }),
  makeFeature({ column: "city", semanticType: "categorical", nullPercentage: 12 }),
  makeFeature({ column: "income", semanticType: "numeric", nullPercentage: 0, hasQualityCritical: true }),
];

const emptyCtx = { correlatedColumns: new Set<string>(), mlColumns: new Set<string>() };

describe("hasActiveFilters", () => {
  it("is false for the default filters", () => {
    expect(hasActiveFilters(DEFAULT_FILTERS)).toBe(false);
  });

  it("is true when any filter is toggled on", () => {
    expect(hasActiveFilters({ ...DEFAULT_FILTERS, numeric: true })).toBe(true);
  });
});

describe("filterFeatureNodes", () => {
  it("returns everything when no filters/search are active", () => {
    expect(filterFeatureNodes(nodes, DEFAULT_FILTERS, "", emptyCtx)).toHaveLength(3);
  });

  it("narrows by search (case-insensitive substring on the real column name)", () => {
    const result = filterFeatureNodes(nodes, DEFAULT_FILTERS, "CIT", emptyCtx);
    expect(result.map((n) => n.column)).toEqual(["city"]);
  });

  it("narrows by a single active filter", () => {
    const result = filterFeatureNodes(nodes, { ...DEFAULT_FILTERS, categorical: true }, "", emptyCtx);
    expect(result.map((n) => n.column)).toEqual(["city"]);
  });

  it("combines multiple active filters as OR", () => {
    const result = filterFeatureNodes(nodes, { ...DEFAULT_FILTERS, categorical: true, qualityWarning: true }, "", emptyCtx);
    expect(result.map((n) => n.column).sort()).toEqual(["city", "income"]);
  });

  it("only counts a column as correlated/ML-related when the real context says so", () => {
    const ctx = { correlatedColumns: new Set(["age"]), mlColumns: new Set(["income"]) };
    const correlated = filterFeatureNodes(nodes, { ...DEFAULT_FILTERS, correlated: true }, "", ctx);
    expect(correlated.map((n) => n.column)).toEqual(["age"]);

    const mlRelated = filterFeatureNodes(nodes, { ...DEFAULT_FILTERS, mlRelated: true }, "", ctx);
    expect(mlRelated.map((n) => n.column)).toEqual(["income"]);
  });

  it("combines search and filters (both must match)", () => {
    const result = filterFeatureNodes(nodes, { ...DEFAULT_FILTERS, numeric: true }, "inc", emptyCtx);
    expect(result.map((n) => n.column)).toEqual(["income"]);
  });
});
