import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AIInsightPanel } from "./AIInsightPanel";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("AIInsightPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the real availability/provider status and links to the full AI tab", () => {
    render(
      <MemoryRouter>
        <AIInsightPanel datasetId="d1" aiStatus={{ enabled: true, provider: "offline", model: null, available: true, reason: null }} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Available")).toBeInTheDocument();
    expect(screen.getByText("provider: offline")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open full AI Insights tab/i })).toHaveAttribute("href", "/datasets/d1/ai");
  });

  it("requests and renders a real grounded dataset summary, labeled as AI interpretation not a computed result", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "d1",
        capability: "dataset_summary",
        computed: { row_count: 10, column_count: 1, missing_percentage: 0, duplicate_row_percentage: 0, quality_finding_count: 0, quality_severity_counts: {}, columns: [] },
        evidence_sources: ["dataset_metadata"],
        ai_explanation: { source: "ai_generated", provider: "offline", model: null, text: "This dataset has 10 rows.", generated_at: "2026-01-01T00:00:00Z" },
        grounded: true,
        limitations: [],
        available: true,
        reason: null,
      }),
    );

    render(
      <MemoryRouter>
        <AIInsightPanel datasetId="d1" aiStatus={{ enabled: true, provider: "offline", model: null, available: true, reason: null }} />
      </MemoryRouter>,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /AI Interpretation/i }));

    expect(await screen.findByText("This dataset has 10 rows.")).toBeInTheDocument();
    expect(screen.getByText(/AI explanation — offline/i)).toBeInTheDocument();
  });
});
