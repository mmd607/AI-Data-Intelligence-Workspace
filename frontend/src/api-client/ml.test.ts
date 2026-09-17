import { afterEach, describe, expect, it, vi } from "vitest";

import { getTaskTypes, trainModel, validateTarget } from "./ml";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("api-client/ml", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("getTaskTypes returns the parsed task type list", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        task_types: [
          { task_type: "regression", label: "Regression", description: "", supported_models: ["linear_regression"] },
        ],
      }),
    );

    const response = await getTaskTypes();
    expect(response.task_types).toHaveLength(1);
  });

  it("validateTarget posts the target column and returns suitability facts", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        dataset_id: "ds1",
        target_column: "price",
        observed: {
          row_count: 10,
          non_null_count: 10,
          null_count: 0,
          unique_count: 10,
          pandas_dtype: "float64",
          semantic_type: "numeric",
        },
        suitable_tasks: [{ task_type: "regression", suitable: true, reason: "Numeric target." }],
        suggested_task: "regression",
        is_suggestion: true,
      }),
    );

    const response = await validateTarget("ds1", { target_column: "price" });
    expect(response.suggested_task).toBe("regression");
    const [, init] = fetchSpy.mock.calls[0];
    expect(JSON.parse(init?.body as string)).toEqual({ target_column: "price" });
  });

  it("trainModel surfaces a structured ML error for an invalid model/task combination", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        { error: { code: "invalid_model_for_task", message: "Model not valid for this task." } },
        400,
      ),
    );

    await expect(
      trainModel("ds1", { target_column: "price", task_type: "regression", model_name: "logistic_regression" }),
    ).rejects.toMatchObject({ code: "invalid_model_for_task" });
  });
});
