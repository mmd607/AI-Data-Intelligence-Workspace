import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, useUniverseStore } from "../state/universeStore";
import type { UniverseGraph } from "./types";
import { UniverseFallback } from "./UniverseFallback";

const graph: UniverseGraph = {
  datasetNode: { id: "dataset", type: "dataset", label: "sales.csv", position: { x: 0, y: 0, z: 0 }, state: "idle", rowCount: 500, columnCount: 2 },
  domainNodes: [
    { id: "domain:profile", type: "domain", domain: "profile", label: "Data Profile", position: { x: 0, y: 0, z: 0 }, state: "idle", available: true, summary: "2 columns profiled" },
    { id: "domain:quality", type: "domain", domain: "quality", label: "Data Quality", position: { x: 0, y: 0, z: 0 }, state: "disabled", available: false, summary: "Not loaded yet" },
    { id: "domain:analytics", type: "domain", domain: "analytics", label: "Analytics", position: { x: 0, y: 0, z: 0 }, state: "idle", available: true, summary: "1 correlation pair" },
    { id: "domain:ml", type: "domain", domain: "ml", label: "ML", position: { x: 0, y: 0, z: 0 }, state: "disabled", available: false, summary: "No model trained yet" },
    { id: "domain:ai", type: "domain", domain: "ai", label: "AI Insights", position: { x: 0, y: 0, z: 0 }, state: "idle", available: true, summary: "offline available" },
  ],
  featureNodesByDomain: {
    profile: [
      { id: "feature:profile:age", type: "feature", domain: "profile", column: "age", label: "age", position: { x: 0, y: 0, z: 0 }, state: "idle", semanticType: "numeric", nullPercentage: 0, hasQualityWarning: false, hasQualityCritical: false },
      { id: "feature:profile:income", type: "feature", domain: "profile", column: "income", label: "income", position: { x: 0, y: 0, z: 0 }, state: "error", semanticType: "numeric", nullPercentage: 40, hasQualityWarning: false, hasQualityCritical: true },
    ],
    analytics: [],
  },
  correlationEdges: [
    { id: "edge:age::income", source: "feature:analytics:age", target: "feature:analytics:income", coefficient: 0.42, observations: 500 },
  ],
  domainConnections: [],
};

beforeEach(() => {
  useUniverseStore.setState({
    selectedNodeId: null,
    hoveredNodeId: null,
    focusedNodeId: null,
    searchQuery: "",
    filters: DEFAULT_FILTERS,
    viewMode: "2d",
  });
});

function renderFallback(reason?: string) {
  return render(
    <MemoryRouter>
      <UniverseFallback graph={graph} datasetId="ds-1" reason={reason} />
    </MemoryRouter>,
  );
}

describe("UniverseFallback", () => {
  it("shows the dataset summary and every domain with its real availability", () => {
    renderFallback();
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText("Data Quality")).toBeInTheDocument();
    expect(screen.getAllByText("Available").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Empty").length).toBeGreaterThan(0);
  });

  it("shows an explanatory reason banner when provided (e.g. 3D failure or no WebGL)", () => {
    renderFallback("3D visualization is unavailable.");
    expect(screen.getByText("3D visualization is unavailable.")).toBeInTheDocument();
  });

  it("lists real feature columns with real quality state, never fabricated", () => {
    renderFallback();
    expect(screen.getByText("age")).toBeInTheDocument();
    expect(screen.getByText("income")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
  });

  it("search narrows the feature table", async () => {
    const user = userEvent.setup();
    renderFallback();
    await user.type(screen.getByLabelText("Search columns"), "inc");
    expect(screen.queryByText("age")).not.toBeInTheDocument();
    expect(screen.getByText("income")).toBeInTheDocument();
  });

  it("shows the real strongest-correlations list", () => {
    renderFallback();
    expect(screen.getByText("age × income")).toBeInTheDocument();
    expect(screen.getByText("0.420")).toBeInTheDocument();
  });

  it("the dataset card's action selects the dataset core node", async () => {
    const user = userEvent.setup();
    renderFallback();
    await user.click(screen.getByRole("button", { name: "View dataset details" }));
    expect(useUniverseStore.getState().selectedNodeId).toBe("dataset");
  });

  it("selecting a feature row updates the shared selection store", async () => {
    const user = userEvent.setup();
    renderFallback();
    await user.click(screen.getByText("age"));
    expect(useUniverseStore.getState().selectedNodeId).toBe("feature:profile:age");
  });
});
