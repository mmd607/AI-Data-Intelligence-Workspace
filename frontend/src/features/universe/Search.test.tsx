import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, useUniverseStore } from "../../state/universeStore";
import type { FeatureNode } from "../../universe/types";
import { Search } from "./Search";

function makeFeature(column: string): FeatureNode {
  return {
    id: `feature:profile:${column}`,
    type: "feature",
    domain: "profile",
    column,
    label: column,
    position: { x: 0, y: 0, z: 0 },
    state: "idle",
    semanticType: "numeric",
    nullPercentage: 0,
    hasQualityWarning: false,
    hasQualityCritical: false,
  };
}

const features = [makeFeature("age"), makeFeature("income"), makeFeature("city")];

beforeEach(() => {
  useUniverseStore.setState({
    selectedNodeId: null,
    hoveredNodeId: null,
    focusedNodeId: null,
    searchQuery: "",
    filters: DEFAULT_FILTERS,
    viewMode: "3d",
  });
});

describe("Search", () => {
  it("shows matching columns as the user types", async () => {
    const user = userEvent.setup();
    render(<Search features={features} />);
    await user.type(screen.getByLabelText("Search columns"), "in");
    expect(screen.getByText(/income/)).toBeInTheDocument();
    expect(screen.queryByText(/^age$/)).not.toBeInTheDocument();
  });

  it("selecting a result focuses (and selects) the real matching node", async () => {
    const user = userEvent.setup();
    render(<Search features={features} />);
    await user.type(screen.getByLabelText("Search columns"), "age");
    await user.click(screen.getByText(/age/));
    expect(useUniverseStore.getState().focusedNodeId).toBe("feature:profile:age");
    expect(useUniverseStore.getState().selectedNodeId).toBe("feature:profile:age");
  });
});
