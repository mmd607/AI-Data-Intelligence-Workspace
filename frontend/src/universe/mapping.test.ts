import { describe, expect, it } from "vitest";

import type {
  AIStatusResponse,
  ColumnProfile,
  CorrelationResult,
  DatasetMetadata,
  DatasetProfile,
  ModelResult,
  QualitySummary,
} from "../api-client";
import { ANALYTICS_PAIR_CAP, buildUniverseGraph, PROFILE_FEATURE_CAP, type BuildUniverseGraphInput } from "./mapping";

function makeColumn(name: string, overrides: Partial<ColumnProfile> = {}): ColumnProfile {
  return {
    name,
    pandas_dtype: "float64",
    semantic_type: "numeric",
    null_count: 0,
    null_percentage: 0,
    unique_count: 10,
    unique_percentage: 100,
    sample_values: [1, 2, 3],
    numeric_stats: null,
    categorical_stats: null,
    datetime_stats: null,
    ...overrides,
  };
}

const dataset: DatasetMetadata = {
  id: "ds-1",
  original_filename: "sales.csv",
  uploaded_at: "2026-01-01T00:00:00Z",
  size_bytes: 1024,
  row_count: 100,
  column_count: 2,
  columns: [
    { name: "age", dtype: "float64" },
    { name: "income", dtype: "float64" },
  ],
  missing_value_count: 0,
  duplicate_row_count: 0,
};

const profile: DatasetProfile = {
  dataset_id: "ds-1",
  row_count: 100,
  column_count: 2,
  memory_usage_bytes: 2048,
  duplicate_row_count: 0,
  duplicate_row_percentage: 0,
  missing: { total_missing_cells: 0, missing_percentage: 0, columns_with_missing: 0 },
  columns: [makeColumn("age"), makeColumn("income")],
  generated_at: "2026-01-01T00:00:00Z",
};

const quality: QualitySummary = {
  dataset_id: "ds-1",
  findings: [
    { code: "high_missing", severity: "warning", column: "age", message: "20% missing", metric: 20, details: {} },
    { code: "constant_column", severity: "critical", column: "income", message: "constant", metric: null, details: {} },
  ],
  finding_count: 2,
  generated_at: "2026-01-01T00:00:00Z",
};

const correlationComputed: CorrelationResult = {
  dataset_id: "ds-1",
  method: "pearson",
  minimum_observations: 3,
  eligible_columns: ["age", "income"],
  pairs: [{ column_a: "age", column_b: "income", coefficient: 0.42, observations: 100 }],
  status: "computed",
  message: null,
  generated_at: "2026-01-01T00:00:00Z",
};

const correlationInsufficient: CorrelationResult = {
  ...correlationComputed,
  pairs: [],
  status: "insufficient_data",
  message: "Not enough numeric columns.",
};

const mlResult: ModelResult = {
  dataset_id: "ds-1",
  target_column: "income",
  task_type: "regression",
  feature_columns: ["age"],
  excluded_columns: [],
  preprocessing: { numeric_features: ["age"], categorical_features: [], numeric_transform: "scale", categorical_transform: "onehot" },
  model_name: "linear_regression",
  training_config: { test_size: 0.2, random_state: 42, stratified: false },
  train_size: 80,
  test_size_actual: 20,
  metrics: { r2: 0.9 },
  unavailable_metrics: {},
  confusion_matrix: null,
  warnings: [],
  limitations: [],
  generated_at: "2026-01-01T00:00:00Z",
};

const aiAvailable: AIStatusResponse = { enabled: true, provider: "offline", model: null, available: true, reason: null };
const aiUnavailable: AIStatusResponse = { enabled: true, provider: "anthropic", model: null, available: false, reason: "No API key configured" };

function baseInput(overrides: Partial<BuildUniverseGraphInput> = {}): BuildUniverseGraphInput {
  return {
    dataset,
    profile: null,
    quality: null,
    correlation: null,
    mlResult: null,
    aiStatus: null,
    ...overrides,
  };
}

describe("buildUniverseGraph — dataset node", () => {
  it("always includes the dataset core with real row/column counts", () => {
    const graph = buildUniverseGraph(baseInput());
    expect(graph.datasetNode.id).toBe("dataset");
    expect(graph.datasetNode.rowCount).toBe(100);
    expect(graph.datasetNode.columnCount).toBe(2);
    expect(graph.datasetNode.label).toBe("sales.csv");
  });
});

describe("buildUniverseGraph — domain nodes", () => {
  it("always produces exactly the 5 fixed domain nodes, dataset-connected", () => {
    const graph = buildUniverseGraph(baseInput());
    expect(graph.domainNodes.map((d) => d.domain)).toEqual(["profile", "quality", "analytics", "ml", "ai"]);
    expect(graph.domainConnections).toHaveLength(5);
    for (const conn of graph.domainConnections) expect(conn.source).toBe("dataset");
  });

  it("marks a domain disabled when its data hasn't loaded", () => {
    const graph = buildUniverseGraph(baseInput());
    for (const domain of graph.domainNodes) {
      expect(domain.available).toBe(false);
      expect(domain.state).toBe("disabled");
    }
  });

  it("marks quality available even with zero findings (endpoint answered, just clean)", () => {
    const graph = buildUniverseGraph(baseInput({ quality: { ...quality, findings: [], finding_count: 0 } }));
    const qualityNode = graph.domainNodes.find((d) => d.domain === "quality")!;
    expect(qualityNode.available).toBe(true);
    expect(qualityNode.state).toBe("idle");
  });

  it("marks analytics available (not disabled) even on insufficient_data — the data was answered, not missing", () => {
    const graph = buildUniverseGraph(baseInput({ correlation: correlationInsufficient }));
    const analyticsNode = graph.domainNodes.find((d) => d.domain === "analytics")!;
    expect(analyticsNode.available).toBe(true);
    expect(analyticsNode.summary).toContain("Not enough numeric columns");
  });

  it("reflects real AI availability/reason, never invents one", () => {
    const unavailableGraph = buildUniverseGraph(baseInput({ aiStatus: aiUnavailable }));
    const aiNode = unavailableGraph.domainNodes.find((d) => d.domain === "ai")!;
    expect(aiNode.available).toBe(false);
    expect(aiNode.summary).toBe("No API key configured");

    const availableGraph = buildUniverseGraph(baseInput({ aiStatus: aiAvailable }));
    expect(availableGraph.domainNodes.find((d) => d.domain === "ai")!.available).toBe(true);
  });

  it("marks ML disabled until a model has actually been trained this session", () => {
    const graph = buildUniverseGraph(baseInput({ mlResult }));
    const mlNode = graph.domainNodes.find((d) => d.domain === "ml")!;
    expect(mlNode.available).toBe(true);
    expect(mlNode.summary).toBe("linear_regression · regression");
  });
});

describe("buildUniverseGraph — feature nodes (profile ring)", () => {
  it("is empty until the profile has loaded", () => {
    expect(buildUniverseGraph(baseInput()).featureNodesByDomain.profile).toEqual([]);
  });

  it("produces one feature node per profiled column, tagged with real semantic type and missingness", () => {
    const graph = buildUniverseGraph(baseInput({ profile }));
    const names = graph.featureNodesByDomain.profile.map((f) => f.column);
    expect(names).toEqual(["age", "income"]);
    expect(graph.featureNodesByDomain.profile[0].semanticType).toBe("numeric");
  });

  it("flags quality warnings/criticals from real findings only, never invented", () => {
    const graph = buildUniverseGraph(baseInput({ profile, quality }));
    const age = graph.featureNodesByDomain.profile.find((f) => f.column === "age")!;
    const income = graph.featureNodesByDomain.profile.find((f) => f.column === "income")!;
    expect(age.hasQualityWarning).toBe(true);
    expect(age.hasQualityCritical).toBe(false);
    expect(age.state).toBe("idle");
    expect(income.hasQualityCritical).toBe(true);
    expect(income.state).toBe("error");
  });

  it("caps the profile ring at PROFILE_FEATURE_CAP without dropping data silently (2D fallback covers the rest)", () => {
    const manyColumns = Array.from({ length: PROFILE_FEATURE_CAP + 15 }, (_, i) => makeColumn(`col_${i}`));
    const bigProfile: DatasetProfile = { ...profile, columns: manyColumns, column_count: manyColumns.length };
    const graph = buildUniverseGraph(baseInput({ profile: bigProfile }));
    expect(graph.featureNodesByDomain.profile).toHaveLength(PROFILE_FEATURE_CAP);
  });

  it("is deterministic across repeated calls with identical input", () => {
    const a = buildUniverseGraph(baseInput({ profile }));
    const b = buildUniverseGraph(baseInput({ profile }));
    expect(a.featureNodesByDomain.profile).toEqual(b.featureNodesByDomain.profile);
  });
});

describe("buildUniverseGraph — correlation edges (analytics ring)", () => {
  it("produces zero edges when correlation hasn't loaded", () => {
    const graph = buildUniverseGraph(baseInput());
    expect(graph.correlationEdges).toEqual([]);
    expect(graph.featureNodesByDomain.analytics).toEqual([]);
  });

  it("produces zero fabricated edges on insufficient_data", () => {
    const graph = buildUniverseGraph(baseInput({ profile, correlation: correlationInsufficient }));
    expect(graph.correlationEdges).toEqual([]);
  });

  it("creates one real edge per correlation pair, carrying the real coefficient", () => {
    const graph = buildUniverseGraph(baseInput({ profile, correlation: correlationComputed }));
    expect(graph.correlationEdges).toHaveLength(1);
    expect(graph.correlationEdges[0].coefficient).toBe(0.42);
    expect(graph.correlationEdges[0].source).toBe("feature:analytics:age");
    expect(graph.correlationEdges[0].target).toBe("feature:analytics:income");
  });

  it("caps at ANALYTICS_PAIR_CAP, keeping only the strongest |coefficient| pairs", () => {
    const manyPairs = Array.from({ length: ANALYTICS_PAIR_CAP + 10 }, (_, i) => ({
      column_a: `a${i}`,
      column_b: `b${i}`,
      coefficient: (i % 2 === 0 ? 1 : -1) * (0.01 + i * 0.001),
      observations: 50,
    }));
    const bigCorrelation: CorrelationResult = { ...correlationComputed, pairs: manyPairs };
    const weakestKeptCoefficient = manyPairs
      .slice()
      .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))[ANALYTICS_PAIR_CAP - 1].coefficient;

    const graph = buildUniverseGraph(baseInput({ profile, correlation: bigCorrelation }));
    expect(graph.correlationEdges).toHaveLength(ANALYTICS_PAIR_CAP);
    const coefficients = graph.correlationEdges.map((e) => Math.abs(e.coefficient));
    expect(Math.min(...coefficients)).toBeCloseTo(Math.abs(weakestKeptCoefficient), 5);
  });
});
