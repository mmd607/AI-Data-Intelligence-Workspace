import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { UploadPage } from "./UploadPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function renderPage() {
  return render(
    <MemoryRouter>
      <UploadPage />
    </MemoryRouter>,
  );
}

describe("UploadPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows a validation error for a non-CSV file dropped onto the dropzone, without calling the server", async () => {
    // A renamed file can bypass the file input's `accept=".csv"` browser-level filter via
    // drag-and-drop, which is exactly the case the client-side extension check guards.
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));
    renderPage();

    const dropzone = screen.getByRole("button", { name: /upload a csv dataset/i });
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });

    expect(await screen.findByText(/unsupported file type/i)).toBeInTheDocument();
    // Only the initial dataset-list GET should have fired — never an upload POST.
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("uploads a valid CSV and shows a loading state while the request is in flight", async () => {
    let resolveUpload!: (value: Response) => void;
    const uploadPromise = new Promise<Response>((resolve) => {
      resolveUpload = resolve;
    });
    vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => {
      if (init?.method === "POST") return uploadPromise;
      return Promise.resolve(jsonResponse([]));
    });

    renderPage();
    const user = userEvent.setup();
    const input = screen.getByLabelText(/upload a csv dataset/i).querySelector("input") as HTMLInputElement;
    const file = new File(["a,b\n1,2"], "data.csv", { type: "text/csv" });
    await user.upload(input, file);

    expect(await screen.findByText(/uploading and parsing/i)).toBeInTheDocument();

    resolveUpload(
      jsonResponse(
        {
          id: "ds1",
          original_filename: "data.csv",
          uploaded_at: "2026-01-01T00:00:00Z",
          size_bytes: 8,
          row_count: 1,
          column_count: 2,
          columns: [
            { name: "a", dtype: "int64" },
            { name: "b", dtype: "int64" },
          ],
          missing_value_count: 0,
          duplicate_row_count: 0,
        },
        201,
      ),
    );

    await waitFor(() => expect(screen.queryByText(/uploading and parsing/i)).not.toBeInTheDocument());
  });

  it("shows a server error and lets the user dismiss it", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => {
      if (init?.method === "POST") {
        return Promise.resolve(jsonResponse({ error: { code: "file_too_large", message: "Too large." } }, 413));
      }
      return Promise.resolve(jsonResponse([]));
    });

    renderPage();
    const user = userEvent.setup();
    const input = screen.getByLabelText(/upload a csv dataset/i).querySelector("input") as HTMLInputElement;
    const file = new File(["a,b\n1,2"], "big.csv", { type: "text/csv" });
    await user.upload(input, file);

    expect(await screen.findByText("Too large.")).toBeInTheDocument();
    await user.click(within(screen.getByText("Too large.").closest("div") as HTMLElement).getByRole("button"));
  });

  it("lists previously uploaded datasets", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse([
        {
          id: "ds1",
          original_filename: "existing.csv",
          uploaded_at: "2026-01-01T00:00:00Z",
          size_bytes: 2048,
          row_count: 5,
          column_count: 3,
        },
      ]),
    );

    renderPage();
    expect(await screen.findByText("existing.csv")).toBeInTheDocument();
  });
});
