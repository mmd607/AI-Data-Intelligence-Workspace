import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { QualityPage } from "./QualityPage";

vi.mock("../workspace/useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => ({
    id: "ds1",
    original_filename: "a.csv",
    uploaded_at: "2026-01-01T00:00:00Z",
    size_bytes: 100,
    row_count: 10,
    column_count: 1,
    columns: [{ name: "a", dtype: "int64" }],
    missing_value_count: 0,
    duplicate_row_count: 0,
  }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("QualityPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders every real finding with its severity and message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        findings: [
          {
            code: "duplicate_rows",
            severity: "warning",
            column: null,
            message: "1 duplicate row(s) found.",
            metric: 1,
            details: {},
          },
        ],
        finding_count: 1,
        generated_at: "2026-01-01T00:00:00Z",
      }),
    );

    render(<QualityPage />);

    expect(await screen.findByText("1 duplicate row(s) found.")).toBeInTheDocument();
    expect(screen.getByText("warning")).toBeInTheDocument();
  });

  it("shows an empty state when there are no findings", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ dataset_id: "ds1", findings: [], finding_count: 0, generated_at: "2026-01-01T00:00:00Z" }),
    );

    render(<QualityPage />);

    expect(await screen.findByText(/no data-quality findings/i)).toBeInTheDocument();
  });
});
