import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { OverviewPage } from "./OverviewPage";

// `useWorkspaceDataset` reads from the parent route's Outlet context, which only exists
// under a real <WorkspaceLayout>; this page is tested in isolation by stubbing it, the
// same pattern the project already uses for the 3D canvas (02_DOCS/TESTING_STRATEGY.md §4).
vi.mock("./useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => ({
    id: "ds1",
    original_filename: "a.csv",
    uploaded_at: "2026-01-01T00:00:00Z",
    size_bytes: 2048,
    row_count: 10,
    column_count: 2,
    columns: [
      { name: "age", dtype: "int64" },
      { name: "category", dtype: "object" },
    ],
    missing_value_count: 1,
    duplicate_row_count: 1,
  }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("OverviewPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders dataset overview stats and the real computed column profile", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        row_count: 10,
        column_count: 2,
        memory_usage_bytes: 4096,
        duplicate_row_count: 1,
        duplicate_row_percentage: 10,
        missing: { total_missing_cells: 1, missing_percentage: 5, columns_with_missing: 1 },
        columns: [
          {
            name: "age",
            pandas_dtype: "int64",
            semantic_type: "numeric",
            null_count: 1,
            null_percentage: 10,
            unique_count: 9,
            unique_percentage: 90,
            sample_values: [25, 30, 35],
            numeric_stats: { min: 25, max: 60, mean: 40, median: 38, std: 10, q1: 30, q3: 50, iqr: 20, zero_count: 0, negative_count: 0, infinite_count: 0 },
            categorical_stats: null,
            datetime_stats: null,
          },
        ],
        generated_at: "2026-01-01T00:00:00Z",
      }),
    );

    render(<OverviewPage />);

    expect(await screen.findByText("age")).toBeInTheDocument();
    // The dataset-level facts come straight from the already-fetched DatasetMetadata.
    expect(screen.getAllByText("10").length).toBeGreaterThan(0);
    expect(screen.getByText("numeric")).toBeInTheDocument();
  });

  it("shows an error state with a retry action when the profile request fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ error: { code: "internal_error", message: "Boom." } }, 500));

    render(<OverviewPage />);

    expect(await screen.findByText("Boom.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });
});
