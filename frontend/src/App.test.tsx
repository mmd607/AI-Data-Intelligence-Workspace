import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

// The 3D scene needs a real WebGL context, which jsdom does not provide. Per
// 02_DOCS/TESTING_STRATEGY.md §4, the 3D layer is tested via logic/state tests, not by
// rendering the actual Canvas in a DOM-only test environment — so it's stubbed here.
vi.mock("./scene/UniversePlaceholder", () => ({
  UniversePlaceholder: () => <div data-testid="universe-placeholder-stub" />,
}));

describe("App", () => {
  it("shows a loading state and then reflects a successful backend connection", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "ok",
          service: "AI Data Intelligence Workspace API",
          environment: "development",
          timestamp: "2026-09-17T00:00:00Z",
        }),
        { status: 200 },
      ),
    );

    render(<App />);

    expect(screen.getByText(/Checking backend/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Backend connected — development/i)).toBeInTheDocument();
    });

    vi.restoreAllMocks();
  });

  it("shows an error state when the backend is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("network down"));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Backend unavailable/i)).toBeInTheDocument();
    });

    vi.restoreAllMocks();
  });
});
