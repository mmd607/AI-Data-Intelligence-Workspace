import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

describe("App", () => {
  it("shows the upload landing page with existing datasets", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: /upload a dataset/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /upload a csv dataset/i })).toBeInTheDocument();
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());

    vi.restoreAllMocks();
  });

  it("shows an error state when the dataset list request fails", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network down"));

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/could not reach the server/i)).toBeInTheDocument();
    });

    vi.restoreAllMocks();
  });

  it("redirects an unknown route back to the upload landing page", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse([]));

    render(
      <MemoryRouter initialEntries={["/does-not-exist"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: /upload a dataset/i })).toBeInTheDocument();
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());

    vi.restoreAllMocks();
  });
});
