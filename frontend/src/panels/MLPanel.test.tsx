import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { ModelResult } from "../api-client";
import { MLPanel } from "./MLPanel";

describe("MLPanel", () => {
  it("shows an empty state and a link to train when no model has been trained this session", () => {
    render(
      <MemoryRouter>
        <MLPanel datasetId="d1" mlResult={null} />
      </MemoryRouter>,
    );
    expect(screen.getByText("No model trained yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open ML tab" })).toHaveAttribute("href", "/datasets/d1/ml");
  });

  it("renders the real trained result's metrics, never a fabricated score", () => {
    const mlResult: ModelResult = {
      dataset_id: "d1",
      target_column: "income",
      task_type: "regression",
      feature_columns: ["age"],
      excluded_columns: [],
      preprocessing: { numeric_features: ["age"], categorical_features: [], numeric_transform: "scale", categorical_transform: "onehot" },
      model_name: "linear_regression",
      training_config: { test_size: 0.2, random_state: 42, stratified: false },
      train_size: 80,
      test_size_actual: 20,
      metrics: { r2: 0.91 },
      unavailable_metrics: {},
      confusion_matrix: null,
      warnings: ["Small test set."],
      limitations: ["Baseline model only."],
      generated_at: "2026-01-01T00:00:00Z",
    };
    render(
      <MemoryRouter>
        <MLPanel datasetId="d1" mlResult={mlResult} />
      </MemoryRouter>,
    );
    expect(screen.getByText(/linear_regression/)).toBeInTheDocument();
    expect(screen.getByText("0.91")).toBeInTheDocument();
    expect(screen.getByText(/Small test set\./)).toBeInTheDocument();
    expect(screen.getByText(/Baseline model only\./)).toBeInTheDocument();
  });
});
