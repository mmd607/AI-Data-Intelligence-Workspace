import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./http";
import { getDataset, listDatasets, uploadDataset } from "./datasets";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("api-client/datasets", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uploadDataset posts multipart form data and returns parsed metadata", async () => {
    const metadata = {
      id: "ds1",
      original_filename: "a.csv",
      uploaded_at: "2026-01-01T00:00:00Z",
      size_bytes: 10,
      row_count: 2,
      column_count: 1,
      columns: [{ name: "a", dtype: "int64" }],
      missing_value_count: 0,
      duplicate_row_count: 0,
    };
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(metadata, 201));

    const file = new File(["a\n1\n2"], "a.csv", { type: "text/csv" });
    const result = await uploadDataset(file);

    expect(result.id).toBe("ds1");
    const [, init] = fetchSpy.mock.calls[0];
    expect(init?.body).toBeInstanceOf(FormData);
  });

  it("uploadDataset surfaces the backend's structured error message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: { code: "unsupported_file_type", message: "Unsupported file type '.txt'." } }, 400),
    );

    const file = new File(["x"], "a.txt");
    await expect(uploadDataset(file)).rejects.toMatchObject({
      message: "Unsupported file type '.txt'.",
      code: "unsupported_file_type",
    });
  });

  it("listDatasets returns the parsed list", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
    await expect(listDatasets()).resolves.toEqual([]);
  });

  it("getDataset throws ApiError with a 404 status for an unknown dataset", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: { code: "dataset_not_found", message: "No dataset with id 'nope'." } }, 404),
    );

    await expect(getDataset("nope")).rejects.toBeInstanceOf(ApiError);
    await expect(getDataset("nope")).rejects.toMatchObject({ status: 404 });
  });
});
