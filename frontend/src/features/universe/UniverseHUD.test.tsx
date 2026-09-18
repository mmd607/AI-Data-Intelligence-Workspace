import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, useUniverseStore } from "../../state/universeStore";
import { UniverseHUD } from "./UniverseHUD";

beforeEach(() => {
  useUniverseStore.setState({
    selectedNodeId: "domain:quality",
    hoveredNodeId: null,
    focusedNodeId: "domain:quality",
    searchQuery: "",
    filters: DEFAULT_FILTERS,
    viewMode: "3d",
  });
});

describe("UniverseHUD", () => {
  it("Reset View clears selection/hover/focus", async () => {
    const user = userEvent.setup();
    render(<UniverseHUD features={[]} webglAvailable />);
    await user.click(screen.getByRole("button", { name: "Reset View" }));
    expect(useUniverseStore.getState().selectedNodeId).toBeNull();
    expect(useUniverseStore.getState().focusedNodeId).toBeNull();
  });

  it("toggles the legend popover", async () => {
    const user = userEvent.setup();
    render(<UniverseHUD features={[]} webglAvailable />);
    expect(screen.queryByText("Node types")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Legend" }));
    expect(screen.getByText("Node types")).toBeInTheDocument();
  });

  it("shows and toggles the 2D/3D switch when WebGL is available", async () => {
    const user = userEvent.setup();
    render(<UniverseHUD features={[]} webglAvailable />);
    const toggle = screen.getByRole("button", { name: "Switch to 2D" });
    await user.click(toggle);
    expect(useUniverseStore.getState().viewMode).toBe("2d");
  });

  it("hides the 2D/3D switch when WebGL is unavailable (there is nothing to switch to)", () => {
    render(<UniverseHUD features={[]} webglAvailable={false} />);
    expect(screen.queryByRole("button", { name: /Switch to/ })).not.toBeInTheDocument();
  });
});
