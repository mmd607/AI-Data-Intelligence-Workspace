import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, useUniverseStore } from "./universeStore";

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

describe("universeStore", () => {
  it("selects a node", () => {
    useUniverseStore.getState().selectNode("domain:quality");
    expect(useUniverseStore.getState().selectedNodeId).toBe("domain:quality");
  });

  it("hovering does not affect selection", () => {
    useUniverseStore.getState().selectNode("domain:quality");
    useUniverseStore.getState().hoverNode("feature:profile:age");
    expect(useUniverseStore.getState().selectedNodeId).toBe("domain:quality");
    expect(useUniverseStore.getState().hoveredNodeId).toBe("feature:profile:age");
  });

  it("focusing a node also selects it", () => {
    useUniverseStore.getState().focusNode("domain:analytics");
    expect(useUniverseStore.getState().focusedNodeId).toBe("domain:analytics");
    expect(useUniverseStore.getState().selectedNodeId).toBe("domain:analytics");
  });

  it("toggles a single filter without affecting the others", () => {
    useUniverseStore.getState().toggleFilter("numeric");
    expect(useUniverseStore.getState().filters.numeric).toBe(true);
    expect(useUniverseStore.getState().filters.categorical).toBe(false);

    useUniverseStore.getState().toggleFilter("numeric");
    expect(useUniverseStore.getState().filters.numeric).toBe(false);
  });

  it("clearFilters resets every filter to false", () => {
    useUniverseStore.getState().toggleFilter("numeric");
    useUniverseStore.getState().toggleFilter("qualityWarning");
    useUniverseStore.getState().clearFilters();
    expect(useUniverseStore.getState().filters).toEqual(DEFAULT_FILTERS);
  });

  it("setSearchQuery updates the query", () => {
    useUniverseStore.getState().setSearchQuery("income");
    expect(useUniverseStore.getState().searchQuery).toBe("income");
  });

  it("setViewMode switches between 3d and 2d", () => {
    useUniverseStore.getState().setViewMode("2d");
    expect(useUniverseStore.getState().viewMode).toBe("2d");
  });

  it("resetView clears selection/hover/focus but leaves search/filters/viewMode alone", () => {
    useUniverseStore.getState().selectNode("domain:ml");
    useUniverseStore.getState().hoverNode("domain:ai");
    useUniverseStore.getState().focusNode("domain:ml");
    useUniverseStore.getState().setSearchQuery("age");
    useUniverseStore.getState().toggleFilter("missing");
    useUniverseStore.getState().setViewMode("2d");

    useUniverseStore.getState().resetView();

    const state = useUniverseStore.getState();
    expect(state.selectedNodeId).toBeNull();
    expect(state.hoveredNodeId).toBeNull();
    expect(state.focusedNodeId).toBeNull();
    expect(state.searchQuery).toBe("age");
    expect(state.filters.missing).toBe(true);
    expect(state.viewMode).toBe("2d");
  });
});
