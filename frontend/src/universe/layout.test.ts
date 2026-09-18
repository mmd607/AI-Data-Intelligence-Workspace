import { describe, expect, it } from "vitest";

import { datasetCorePosition, domainNodePosition, featureRingPositions, hashString, seededRandom01 } from "./layout";

describe("hashString / seededRandom01", () => {
  it("is deterministic for the same input", () => {
    expect(hashString("dataset-a")).toBe(hashString("dataset-a"));
    expect(seededRandom01(hashString("dataset-a"))).toBe(seededRandom01(hashString("dataset-a")));
  });

  it("differs for different input", () => {
    expect(hashString("dataset-a")).not.toBe(hashString("dataset-b"));
  });

  it("returns a value in [0, 1)", () => {
    const v = seededRandom01(hashString("anything"));
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThan(1);
  });
});

describe("datasetCorePosition", () => {
  it("is always the origin", () => {
    expect(datasetCorePosition()).toEqual({ x: 0, y: 0, z: 0 });
  });
});

describe("domainNodePosition", () => {
  it("is deterministic per domain", () => {
    expect(domainNodePosition("profile")).toEqual(domainNodePosition("profile"));
  });

  it("places different domains at different positions", () => {
    const positions = ["profile", "quality", "analytics", "ml", "ai"].map((d) =>
      domainNodePosition(d as "profile"),
    );
    const unique = new Set(positions.map((p) => `${p.x.toFixed(4)},${p.z.toFixed(4)}`));
    expect(unique.size).toBe(5);
  });
});

describe("featureRingPositions", () => {
  it("returns an empty array for zero columns", () => {
    expect(featureRingPositions("dataset-a", "profile", 0)).toEqual([]);
  });

  it("is deterministic for the same dataset/domain/count", () => {
    const a = featureRingPositions("dataset-a", "profile", 10);
    const b = featureRingPositions("dataset-a", "profile", 10);
    expect(a).toEqual(b);
  });

  it("returns exactly `count` positions", () => {
    expect(featureRingPositions("dataset-a", "profile", 7)).toHaveLength(7);
  });

  it("produces a different arrangement for a different dataset id", () => {
    const a = featureRingPositions("dataset-a", "profile", 10);
    const b = featureRingPositions("dataset-b", "profile", 10);
    expect(a).not.toEqual(b);
  });

  it("centers the ring around the domain node's own position", () => {
    const center = domainNodePosition("analytics");
    const positions = featureRingPositions("dataset-a", "analytics", 20);
    const avgX = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
    const avgZ = positions.reduce((sum, p) => sum + p.z, 0) / positions.length;
    expect(avgX).toBeCloseTo(center.x, 0);
    expect(avgZ).toBeCloseTo(center.z, 0);
  });
});
