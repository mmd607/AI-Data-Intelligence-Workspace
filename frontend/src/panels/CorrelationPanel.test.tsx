import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { CorrelationResult } from "../api-client";
import { CorrelationPanel } from "./CorrelationPanel";

const base: CorrelationResult = {
  dataset_id: "d1",
  method: "pearson",
  minimum_observations: 3,
  eligible_columns: ["age", "income"],
  pairs: [],
  status: "computed",
  message: null,
  generated_at: "2026-01-01T00:00:00Z",
};

describe("CorrelationPanel", () => {
  it("shows a not-loaded state before data arrives", () => {
    render(<CorrelationPanel correlation={null} />);
    expect(screen.getByText("Not loaded yet")).toBeInTheDocument();
  });

  it("surfaces the real insufficient_data reason, never a fabricated coefficient", () => {
    render(<CorrelationPanel correlation={{ ...base, status: "insufficient_data", message: "Not enough numeric columns." }} />);
    expect(screen.getByText("Not enough data for correlation")).toBeInTheDocument();
    expect(screen.getByText("Not enough numeric columns.")).toBeInTheDocument();
  });

  it("renders every real pair sorted by strength, with a causation disclaimer", () => {
    render(
      <CorrelationPanel
        correlation={{
          ...base,
          pairs: [
            { column_a: "age", column_b: "income", coefficient: 0.2, observations: 90 },
            { column_a: "age", column_b: "score", coefficient: -0.8, observations: 90 },
          ],
        }}
      />,
    );
    const items = screen.getAllByText(/×/);
    expect(items[0]).toHaveTextContent("age × score");
    expect(items[1]).toHaveTextContent("age × income");
    expect(screen.getByText(/does not establish causation/)).toBeInTheDocument();
  });
});
