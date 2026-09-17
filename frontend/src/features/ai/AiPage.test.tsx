import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { DatasetSessionProvider } from "../../state/DatasetSessionContext";
import { AiPage } from "./AiPage";

vi.mock("../workspace/useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => ({
    id: "ds1",
    original_filename: "a.csv",
    uploaded_at: "2026-01-01T00:00:00Z",
    size_bytes: 100,
    row_count: 10,
    column_count: 1,
    columns: [{ name: "age", dtype: "int64" }],
    missing_value_count: 0,
    duplicate_row_count: 0,
  }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderPage() {
  return render(
    <DatasetSessionProvider>
      <AiPage />
    </DatasetSessionProvider>,
  );
}

describe("AiPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the AI as available and renders a grounded dataset-summary explanation on request", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
      const path = String(url);
      if (path.includes("/ai/status")) {
        return Promise.resolve(jsonResponse({ enabled: true, provider: "offline", model: null, available: true, reason: null }));
      }
      if (path.includes("/ai/analyze")) {
        return Promise.resolve(
          jsonResponse({
            dataset_id: "ds1",
            capability: "dataset_summary",
            computed: { row_count: 10, column_count: 1, missing_percentage: 0, duplicate_row_percentage: 0, quality_finding_count: 0, quality_severity_counts: {}, columns: [] },
            evidence_sources: ["dataset_metadata"],
            ai_explanation: {
              source: "ai_generated",
              provider: "offline",
              model: null,
              text: "FACT: This dataset has 10 rows and 1 columns.",
              generated_at: "2026-01-01T00:00:00Z",
            },
            grounded: true,
            limitations: ["The dataset's domain/business purpose is not known and is not claimed."],
            available: true,
            reason: null,
          }),
        );
      }
      throw new Error(`Unhandled fetch: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();

    expect(await screen.findByText("Available")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /dataset summary/i }));

    expect(await screen.findByText(/FACT: This dataset has 10 rows/)).toBeInTheDocument();
    expect(screen.getByText(/AI explanation — offline/i)).toBeInTheDocument();
    expect(screen.getByText("Dataset Profile")).toBeInTheDocument();
  });

  it("shows the AI-unavailable notice while still rendering real computed data", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
      const path = String(url);
      if (path.includes("/ai/status")) {
        return Promise.resolve(jsonResponse({ enabled: true, provider: "anthropic", model: null, available: false, reason: "missing API key" }));
      }
      if (path.includes("/ai/analyze")) {
        return Promise.resolve(
          jsonResponse({
            dataset_id: "ds1",
            capability: "dataset_summary",
            computed: { row_count: 10, column_count: 1, missing_percentage: 0, duplicate_row_percentage: 0, quality_finding_count: 0, quality_severity_counts: {}, columns: [] },
            evidence_sources: ["dataset_metadata"],
            ai_explanation: null,
            grounded: true,
            limitations: [],
            available: false,
            reason: "missing API key",
          }),
        );
      }
      throw new Error(`Unhandled fetch: ${path}`);
    });

    renderPage();
    const user = userEvent.setup();

    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /dataset summary/i }));

    expect(await screen.findByText(/AI analytics is currently unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/deterministic analytics remain available/i)).toBeInTheDocument();
  });

  it("disables the ML-explanation capability until a model has been trained this session", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ enabled: true, provider: "offline", model: null, available: true, reason: null }),
    );

    renderPage();
    expect(await screen.findByText("Available")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ml result/i })).toBeDisabled();
  });
});
