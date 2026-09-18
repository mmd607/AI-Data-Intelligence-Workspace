import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { QualitySummary } from "../api-client";
import { QualityPanel } from "./QualityPanel";

describe("QualityPanel", () => {
  it("shows a not-loaded state before data arrives", () => {
    render(<QualityPanel quality={null} />);
    expect(screen.getByText("Not loaded yet")).toBeInTheDocument();
  });

  it("shows a clean-pass empty state for zero findings, never a fabricated score", () => {
    const quality: QualitySummary = { dataset_id: "d1", findings: [], finding_count: 0, generated_at: "2026-01-01T00:00:00Z" };
    render(<QualityPanel quality={quality} />);
    expect(screen.getByText("No data-quality findings")).toBeInTheDocument();
  });

  it("renders every real finding with its severity and message", () => {
    const quality: QualitySummary = {
      dataset_id: "d1",
      findings: [
        { code: "high_missing", severity: "warning", column: "age", message: "20% missing values", metric: 20, details: {} },
      ],
      finding_count: 1,
      generated_at: "2026-01-01T00:00:00Z",
    };
    render(<QualityPanel quality={quality} />);
    expect(screen.getByText("20% missing values")).toBeInTheDocument();
    expect(screen.getByText("warning")).toBeInTheDocument();
    expect(screen.getByText("· age")).toBeInTheDocument();
  });
});
