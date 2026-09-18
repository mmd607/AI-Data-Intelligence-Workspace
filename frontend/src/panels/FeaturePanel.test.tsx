import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ColumnProfile } from "../api-client";
import { FeaturePanel } from "./FeaturePanel";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

const numericColumn: ColumnProfile = {
  name: "age",
  pandas_dtype: "float64",
  semantic_type: "numeric",
  null_count: 2,
  null_percentage: 4,
  unique_count: 40,
  unique_percentage: 80,
  sample_values: [21, 34, null],
  numeric_stats: { min: 18, max: 65, mean: 34.2, median: 33, std: 8.1, q1: 27, q3: 41, iqr: 14, zero_count: 0, negative_count: 0, infinite_count: 0 },
  categorical_stats: null,
  datetime_stats: null,
};

describe("FeaturePanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders real numeric statistics and quality badges, never invented values", () => {
    render(<FeaturePanel datasetId="d1" column={numericColumn} hasQualityWarning={false} hasQualityCritical={true} />);
    expect(screen.getByText("34.2")).toBeInTheDocument();
    expect(screen.getByText("quality: critical")).toBeInTheDocument();
    expect(screen.getByText("21, 34, ∅")).toBeInTheDocument();
  });

  it("requests and renders a real, grounded AI column insight on demand", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "d1",
        capability: "column_insight",
        computed: { dataset_id: "d1", column_name: "age", pandas_dtype: "float64", semantic_type: "numeric", null_count: 2, null_percentage: 4, unique_count: 40, unique_percentage: 80, sample_values: [], numeric_stats: null, categorical_stats: null, datetime_stats: null },
        evidence_sources: ["column_statistics"],
        ai_explanation: { source: "ai_generated", provider: "offline", model: null, text: "Column age is mostly numeric with few gaps.", generated_at: "2026-01-01T00:00:00Z" },
        grounded: true,
        limitations: [],
        available: true,
        reason: null,
      }),
    );

    render(<FeaturePanel datasetId="d1" column={numericColumn} hasQualityWarning={false} hasQualityCritical={false} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /AI column insight/i }));

    expect(await screen.findByText(/mostly numeric with few gaps/)).toBeInTheDocument();
    expect(screen.getByText(/AI explanation — offline/i)).toBeInTheDocument();
  });
});
