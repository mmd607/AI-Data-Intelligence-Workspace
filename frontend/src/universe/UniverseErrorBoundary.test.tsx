import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { UniverseErrorBoundary } from "./UniverseErrorBoundary";

function Bomb(): never {
  throw new Error("scene exploded");
}

describe("UniverseErrorBoundary", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children when nothing throws", () => {
    render(
      <UniverseErrorBoundary fallback={<p>3D visualization is unavailable.</p>}>
        <p>the scene</p>
      </UniverseErrorBoundary>,
    );
    expect(screen.getByText("the scene")).toBeInTheDocument();
  });

  it("renders the fallback and logs, without crashing the rest of the app, when a child throws", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <UniverseErrorBoundary fallback={<p>3D visualization is unavailable.</p>}>
        <Bomb />
      </UniverseErrorBoundary>,
    );

    expect(screen.getByText("3D visualization is unavailable.")).toBeInTheDocument();
  });
});
