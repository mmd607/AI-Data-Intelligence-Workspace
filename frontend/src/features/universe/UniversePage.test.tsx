import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { DatasetSessionProvider } from "../../state/DatasetSessionContext";
import { DEFAULT_FILTERS, useUniverseStore } from "../../state/universeStore";
import * as tiers from "../../universe/tiers";
import { UniversePage } from "./UniversePage";

const dataset: DatasetMetadata = {
  id: "ds1",
  original_filename: "sales.csv",
  uploaded_at: "2026-01-01T00:00:00Z",
  size_bytes: 2048,
  row_count: 500,
  column_count: 2,
  columns: [
    { name: "age", dtype: "float64" },
    { name: "income", dtype: "float64" },
  ],
  missing_value_count: 0,
  duplicate_row_count: 0,
};

vi.mock("../workspace/useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => dataset,
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderPage() {
  return render(
    <MemoryRouter>
      <DatasetSessionProvider>
        <UniversePage />
      </DatasetSessionProvider>
    </MemoryRouter>,
  );
}

const FORCED_2D_TIER: tiers.TierResult = { tier: "low", webglAvailable: false, forceFallback: true, featureNodeCap: 30 };
const MOBILE_TIER: tiers.TierResult = { tier: "low", webglAvailable: true, forceFallback: true, featureNodeCap: 30 };

beforeEach(() => {
  useUniverseStore.setState({
    selectedNodeId: null,
    hoveredNodeId: null,
    focusedNodeId: null,
    searchQuery: "",
    filters: DEFAULT_FILTERS,
    viewMode: "3d",
  });
  // No WebGL/jsdom test environment -> force the 2D fallback path, matching
  // TESTING_STRATEGY.md §4's "no pixel-level 3D rendering tests" — the 3D scene's own
  // logic is covered at the unit level (mapping/layout/tiers/visualState), not here.
  vi.spyOn(tiers, "detectPerformanceTier").mockReturnValue(FORCED_2D_TIER);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("UniversePage", () => {
  it("renders the real dataset core and every domain, even before profile/quality/correlation/AI status resolve", () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {})); // never resolves
    renderPage();
    expect(screen.getByText("sales.csv")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Data Quality")).toBeInTheDocument();
    expect(screen.getAllByText("Not loaded yet").length).toBeGreaterThan(0);
  });

  it("wires real fetched data into the graph once every request resolves", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
      const path = String(url);
      if (path.includes("/profile")) {
        return Promise.resolve(
          jsonResponse({
            dataset_id: "ds1",
            row_count: 500,
            column_count: 2,
            memory_usage_bytes: 4096,
            duplicate_row_count: 0,
            duplicate_row_percentage: 0,
            missing: { total_missing_cells: 0, missing_percentage: 0, columns_with_missing: 0 },
            columns: [
              { name: "age", pandas_dtype: "float64", semantic_type: "numeric", null_count: 0, null_percentage: 0, unique_count: 50, unique_percentage: 10, sample_values: [1], numeric_stats: null, categorical_stats: null, datetime_stats: null },
              { name: "income", pandas_dtype: "float64", semantic_type: "numeric", null_count: 0, null_percentage: 0, unique_count: 50, unique_percentage: 10, sample_values: [1], numeric_stats: null, categorical_stats: null, datetime_stats: null },
            ],
            generated_at: "2026-01-01T00:00:00Z",
          }),
        );
      }
      if (path.includes("/quality")) {
        return Promise.resolve(jsonResponse({ dataset_id: "ds1", findings: [], finding_count: 0, generated_at: "2026-01-01T00:00:00Z" }));
      }
      if (path.includes("/correlation")) {
        return Promise.resolve(
          jsonResponse({
            dataset_id: "ds1",
            method: "pearson",
            minimum_observations: 3,
            eligible_columns: ["age", "income"],
            pairs: [{ column_a: "age", column_b: "income", coefficient: 0.55, observations: 500 }],
            status: "computed",
            message: null,
            generated_at: "2026-01-01T00:00:00Z",
          }),
        );
      }
      if (path.includes("/ai/status")) {
        return Promise.resolve(jsonResponse({ enabled: true, provider: "offline", model: null, available: true, reason: null }));
      }
      throw new Error(`Unhandled fetch: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("age × income")).toBeInTheDocument();
    expect(screen.getByText("0.550")).toBeInTheDocument();
    expect(screen.getByText("0 findings")).toBeInTheDocument();
  });

  it("selecting the dataset core opens the DatasetPanel", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ error: { code: "not_mocked", message: "n/a" } }, 404));
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "View dataset details" }));
    expect(await screen.findByRole("complementary", { name: "sales.csv" })).toBeInTheDocument();
  });

  it("Escape clears the selection and closes the panel", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ error: { code: "not_mocked", message: "n/a" } }, 404));
    renderPage();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "View dataset details" }));
    expect(await screen.findByRole("complementary")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });

  it("offers a 'Try 3D Universe' affordance when WebGL is available but the mobile default chose 2D", () => {
    vi.mocked(tiers.detectPerformanceTier).mockReturnValue(MOBILE_TIER);
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.getByRole("button", { name: "Try 3D Universe" })).toBeInTheDocument();
  });

  it("does not offer a 3D toggle when WebGL itself is unavailable", () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.queryByRole("button", { name: "Try 3D Universe" })).not.toBeInTheDocument();
  });
});
