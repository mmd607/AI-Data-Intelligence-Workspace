import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Legend } from "./Legend";

describe("Legend", () => {
  it("documents every visual encoding used in the scene", () => {
    render(<Legend />);
    expect(screen.getByText("Node types")).toBeInTheDocument();
    expect(screen.getByText(/missing-value percentage/)).toBeInTheDocument();
    expect(screen.getByText(/strength of correlation/)).toBeInTheDocument();
    expect(screen.getByText(/never causation/)).toBeInTheDocument();
  });
});
