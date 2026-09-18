import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { DatasetMetadata } from "../api-client";
import { DatasetPanel } from "./DatasetPanel";

const dataset: DatasetMetadata = {
  id: "d1",
  original_filename: "sales.csv",
  uploaded_at: "2026-01-01T00:00:00Z",
  size_bytes: 2048,
  row_count: 500,
  column_count: 3,
  columns: [],
  missing_value_count: 0,
  duplicate_row_count: 2,
};

describe("DatasetPanel", () => {
  it("shows real dataset stats and a not-loaded badge for domains without data yet", () => {
    render(
      <MemoryRouter>
        <DatasetPanel dataset={dataset} profile={null} quality={null} correlation={null} mlResult={null} aiStatus={null} />
      </MemoryRouter>,
    );
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getAllByText("Not loaded").length).toBeGreaterThan(0);
  });

  it("reflects real availability once each domain's data has loaded", () => {
    render(
      <MemoryRouter>
        <DatasetPanel
          dataset={dataset}
          profile={null}
          quality={{ dataset_id: "d1", findings: [], finding_count: 0, generated_at: "2026-01-01T00:00:00Z" }}
          correlation={null}
          mlResult={null}
          aiStatus={{ enabled: true, provider: "offline", model: null, available: true, reason: null }}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("No findings")).toBeInTheDocument();
    expect(screen.getByText("offline available")).toBeInTheDocument();
  });

  it("links into every existing 2D tab", () => {
    render(
      <MemoryRouter>
        <DatasetPanel dataset={dataset} profile={null} quality={null} correlation={null} mlResult={null} aiStatus={null} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Quality" })).toHaveAttribute("href", "/datasets/d1/quality");
    expect(screen.getByRole("link", { name: "AI Insights" })).toHaveAttribute("href", "/datasets/d1/ai");
  });
});
