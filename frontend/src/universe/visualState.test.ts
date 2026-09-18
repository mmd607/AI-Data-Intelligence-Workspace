import { describe, expect, it } from "vitest";

import { resolveNodeVisualState } from "./visualState";

describe("resolveNodeVisualState", () => {
  it("defaults to idle", () => {
    expect(resolveNodeVisualState({ available: true })).toBe("idle");
  });

  it("shows hover only when available and not selected", () => {
    expect(resolveNodeVisualState({ available: true, hovered: true })).toBe("hover");
  });

  it("selected takes priority over hover", () => {
    expect(resolveNodeVisualState({ available: true, hovered: true, selected: true })).toBe("selected");
  });

  it("disabled takes priority over hover/selected (no data yet)", () => {
    expect(resolveNodeVisualState({ available: false, hovered: true, selected: true })).toBe("disabled");
  });

  it("loading takes priority over disabled/selected", () => {
    expect(resolveNodeVisualState({ available: false, loading: true, selected: true })).toBe("loading");
  });

  it("error takes the highest priority of all", () => {
    expect(resolveNodeVisualState({ available: true, error: true, loading: true, selected: true })).toBe("error");
  });
});
