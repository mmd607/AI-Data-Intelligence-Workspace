import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DatasetSessionProvider } from "../../state/DatasetSessionContext";
import { QaPanel } from "./QaPanel";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderPanel() {
  return render(
    <DatasetSessionProvider>
      <QaPanel datasetId="ds1" />
    </DatasetSessionProvider>,
  );
}

describe("QaPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("asks a question and renders the grounded deterministic answer plus the AI explanation", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        question: "How many rows are duplicated?",
        question_category: "deterministic_lookup",
        computed: {
          dataset_id: "ds1",
          question: "How many rows are duplicated?",
          question_category: "deterministic_lookup",
          resolved_answer: "1 row(s) are exact duplicates (10.0% of 10 total rows).",
        },
        evidence_sources: ["dataset_metadata", "quality_report", "correlation_report"],
        ai_explanation: {
          source: "ai_generated",
          provider: "offline",
          model: null,
          text: "FACT: 1 row(s) are exact duplicates (10.0% of 10 total rows).",
          generated_at: "2026-01-01T00:00:00Z",
        },
        grounded: true,
        limitations: [],
        available: true,
        reason: null,
      }),
    );

    renderPanel();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /how many rows are duplicated\?/i }));

    expect(await screen.findByText("1 row(s) are exact duplicates (10.0% of 10 total rows).")).toBeInTheDocument();
    expect(screen.getByText(/AI explanation — offline/i)).toBeInTheDocument();
  });

  it("shows an unsupported-question state without fabricating an answer", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        question: "What was the model's F1 score?",
        question_category: "unsupported",
        computed: { dataset_id: "ds1", question: "What was the model's F1 score?", question_category: "unsupported", resolved_answer: null },
        evidence_sources: ["dataset_metadata", "quality_report", "correlation_report"],
        ai_explanation: {
          source: "ai_generated",
          provider: "offline",
          model: null,
          text: "The available dataset evidence does not contain enough information to determine this.",
          generated_at: "2026-01-01T00:00:00Z",
        },
        grounded: true,
        limitations: ["The available dataset evidence does not support this question."],
        available: true,
        reason: null,
      }),
    );

    renderPanel();
    const user = userEvent.setup();

    await user.type(screen.getByPlaceholderText(/ask about this dataset/i), "What was the model's F1 score?");
    await user.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(await screen.findByText("unsupported")).toBeInTheDocument();
    expect(screen.queryByText(/^1 row/)).not.toBeInTheDocument();
  });
});
