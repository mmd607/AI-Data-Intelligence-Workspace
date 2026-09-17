import { afterEach, describe, expect, it, vi } from "vitest";

import { analyzeDatasetSummary, getAiStatus, queryDataset } from "./ai";
import { ApiError } from "./http";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("api-client/ai", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getAiStatus returns the parsed status", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ enabled: true, provider: "offline", model: null, available: true, reason: null }),
    );

    const status = await getAiStatus();
    expect(status.provider).toBe("offline");
    expect(status.available).toBe(true);
  });

  it("analyzeDatasetSummary returns computed evidence alongside the AI explanation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        capability: "dataset_summary",
        computed: { row_count: 10, column_count: 2 },
        evidence_sources: ["dataset_metadata"],
        ai_explanation: {
          source: "ai_generated",
          provider: "offline",
          model: null,
          text: "10 rows.",
          generated_at: "2026-01-01T00:00:00Z",
        },
        grounded: true,
        limitations: [],
        available: true,
        reason: null,
      }),
    );

    const response = await analyzeDatasetSummary("ds1");
    expect(response.computed.row_count).toBe(10);
    expect(response.ai_explanation?.text).toBe("10 rows.");
  });

  it("queryDataset surfaces a validation error for an empty question", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: [{ loc: ["body", "question"], msg: "Field required" }] }, 422),
    );

    await expect(queryDataset("ds1", { question: "" })).rejects.toBeInstanceOf(ApiError);
    await expect(queryDataset("ds1", { question: "" })).rejects.toMatchObject({ status: 422 });
  });
});
