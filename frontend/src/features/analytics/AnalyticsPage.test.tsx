import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { AnalyticsPage } from "./AnalyticsPage";

vi.mock("../workspace/useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => ({
    id: "ds1",
    original_filename: "a.csv",
    uploaded_at: "2026-01-01T00:00:00Z",
    size_bytes: 100,
    row_count: 10,
    column_count: 2,
    columns: [
      { name: "x", dtype: "int64" },
      { name: "y", dtype: "int64" },
    ],
    missing_value_count: 0,
    duplicate_row_count: 0,
  }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function mockFetchByPath(handlers: Record<string, unknown>) {
  vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
    const path = String(url);
    const match = Object.entries(handlers).find(([key]) => path.includes(key));
    if (!match) throw new Error(`Unhandled fetch: ${path}`);
    return Promise.resolve(jsonResponse(match[1]));
  });
}

describe("AnalyticsPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders real histogram bins and correlation pairs from the backend", async () => {
    mockFetchByPath({
      "/distribution": {
        dataset_id: "ds1",
        columns: [
          {
            column: "x",
            bin_count: 2,
            bins: [
              { bin_start: 0, bin_end: 5, count: 3 },
              { bin_start: 5, bin_end: 10, count: 7 },
            ],
            min: 0,
            max: 10,
          },
        ],
        skipped_columns: [],
        generated_at: "2026-01-01T00:00:00Z",
      },
      "/correlation": {
        dataset_id: "ds1",
        method: "pearson",
        minimum_observations: 3,
        eligible_columns: ["x", "y"],
        pairs: [{ column_a: "x", column_b: "y", coefficient: 0.82, observations: 10 }],
        status: "computed",
        message: null,
        generated_at: "2026-01-01T00:00:00Z",
      },
    });

    render(<AnalyticsPage />);

    expect(await screen.findByText("x")).toBeInTheDocument();
    expect(await screen.findByText("x × y")).toBeInTheDocument();
    expect(await screen.findByText("0.820")).toBeInTheDocument();
    expect(await screen.findByText(/however strong, describes a statistical association only/i)).toBeInTheDocument();
  });

  it("shows the insufficient-data message instead of a fabricated correlation", async () => {
    mockFetchByPath({
      "/distribution": { dataset_id: "ds1", columns: [], skipped_columns: ["x", "y"], generated_at: "2026-01-01T00:00:00Z" },
      "/correlation": {
        dataset_id: "ds1",
        method: "pearson",
        minimum_observations: 3,
        eligible_columns: [],
        pairs: [],
        status: "insufficient_data",
        message: "At least 2 numeric columns are required.",
        generated_at: "2026-01-01T00:00:00Z",
      },
    });

    render(<AnalyticsPage />);

    expect(await screen.findByText(/not enough data for correlation/i)).toBeInTheDocument();
    expect(screen.getByText("At least 2 numeric columns are required.")).toBeInTheDocument();
    expect(await screen.findByText(/no numeric columns to plot/i)).toBeInTheDocument();
  });
});
