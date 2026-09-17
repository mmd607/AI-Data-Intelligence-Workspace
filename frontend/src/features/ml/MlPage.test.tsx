import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DatasetMetadata } from "../../api-client";
import { DatasetSessionProvider } from "../../state/DatasetSessionContext";
import { MlPage } from "./MlPage";

vi.mock("../workspace/useWorkspaceDataset", () => ({
  useWorkspaceDataset: (): DatasetMetadata => ({
    id: "ds1",
    original_filename: "a.csv",
    uploaded_at: "2026-01-01T00:00:00Z",
    size_bytes: 100,
    row_count: 40,
    column_count: 2,
    columns: [
      { name: "price", dtype: "float64" },
      { name: "age", dtype: "int64" },
    ],
    missing_value_count: 0,
    duplicate_row_count: 0,
  }),
}));

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function mockFetchByPath(handlers: Array<[string, unknown, number?]>) {
  vi.spyOn(globalThis, "fetch").mockImplementation((url, init) => {
    const path = String(url);
    const method = init?.method ?? "GET";
    const match = handlers.find(([key]) => path.includes(key));
    if (!match) throw new Error(`Unhandled fetch: ${method} ${path}`);
    return Promise.resolve(jsonResponse(match[1], match[2] ?? 200));
  });
}

function renderPage() {
  return render(
    <DatasetSessionProvider>
      <MlPage />
    </DatasetSessionProvider>,
  );
}

describe("MlPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("walks target selection → validation → training and renders real metrics", async () => {
    mockFetchByPath([
      [
        "/ml/task-types",
        {
          task_types: [
            { task_type: "regression", label: "Regression", description: "", supported_models: ["linear_regression"] },
          ],
        },
      ],
      [
        "/validate-target",
        {
          dataset_id: "ds1",
          target_column: "price",
          observed: { row_count: 40, non_null_count: 40, null_count: 0, unique_count: 40, pandas_dtype: "float64", semantic_type: "numeric" },
          suitable_tasks: [{ task_type: "regression", suitable: true, reason: "Numeric target." }],
          suggested_task: "regression",
          is_suggestion: true,
        },
      ],
      [
        "/train",
        {
          dataset_id: "ds1",
          target_column: "price",
          task_type: "regression",
          feature_columns: ["age"],
          excluded_columns: [],
          preprocessing: { numeric_features: ["age"], categorical_features: [], numeric_transform: "", categorical_transform: "" },
          model_name: "linear_regression",
          training_config: { test_size: 0.2, random_state: 42, stratified: false },
          train_size: 32,
          test_size_actual: 8,
          metrics: { rmse: 12.34, r2: 0.5 },
          unavailable_metrics: {},
          confusion_matrix: null,
          warnings: ["Only 40 usable rows."],
          limitations: ["Baseline model only."],
          generated_at: "2026-01-01T00:00:00Z",
        },
      ],
    ]);

    renderPage();
    const user = userEvent.setup();

    await user.selectOptions(await screen.findByLabelText(/target column/i), "price");
    expect(await screen.findByText(/suggested task/i)).toBeInTheDocument();

    await user.selectOptions(await screen.findByLabelText(/^model$/i), "linear_regression");
    await user.click(screen.getByRole("button", { name: /train baseline model/i }));

    expect(await screen.findByText("12.34")).toBeInTheDocument();
    expect(await screen.findByText(/only 40 usable rows/i)).toBeInTheDocument();
    expect(await screen.findByText(/baseline model only/i)).toBeInTheDocument();
  });

  it("shows a structured error when training fails", async () => {
    mockFetchByPath([
      ["/ml/task-types", { task_types: [{ task_type: "regression", label: "Regression", description: "", supported_models: ["linear_regression"] }] }],
      [
        "/validate-target",
        {
          dataset_id: "ds1",
          target_column: "price",
          observed: { row_count: 40, non_null_count: 40, null_count: 0, unique_count: 40, pandas_dtype: "float64", semantic_type: "numeric" },
          suitable_tasks: [{ task_type: "regression", suitable: true, reason: "Numeric target." }],
          suggested_task: "regression",
          is_suggestion: true,
        },
      ],
      ["/train", { error: { code: "insufficient_rows", message: "Not enough rows to train." } }, 400],
    ]);

    renderPage();
    const user = userEvent.setup();

    await user.selectOptions(await screen.findByLabelText(/target column/i), "price");
    await user.selectOptions(await screen.findByLabelText(/^model$/i), "linear_regression");
    await user.click(screen.getByRole("button", { name: /train baseline model/i }));

    expect(await screen.findByText("Not enough rows to train.")).toBeInTheDocument();
  });
});
