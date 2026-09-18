import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { detectPerformanceTier, probeWebGLAvailable, usePrefersReducedMotion } from "./tiers";

describe("probeWebGLAvailable", () => {
  it("returns true when a webgl context is obtainable", () => {
    const fakeDoc = {
      createElement: () => ({ getContext: () => ({}) }),
    } as unknown as Document;
    expect(probeWebGLAvailable(fakeDoc)).toBe(true);
  });

  it("returns false when no webgl context is obtainable", () => {
    const fakeDoc = {
      createElement: () => ({ getContext: () => null }),
    } as unknown as Document;
    expect(probeWebGLAvailable(fakeDoc)).toBe(false);
  });

  it("returns false rather than throwing if context creation errors", () => {
    const fakeDoc = {
      createElement: () => ({
        getContext: () => {
          throw new Error("no gpu");
        },
      }),
    } as unknown as Document;
    expect(probeWebGLAvailable(fakeDoc)).toBe(false);
  });
});

describe("detectPerformanceTier", () => {
  it("forces the 2D fallback when WebGL is unavailable, regardless of viewport", () => {
    const result = detectPerformanceTier({ webglAvailable: false, windowWidth: 1920, hardwareConcurrency: 16 });
    expect(result.tier).toBe("low");
    expect(result.forceFallback).toBe(true);
  });

  it("defaults mobile widths to the 2D fallback even with WebGL and strong hardware", () => {
    const result = detectPerformanceTier({ webglAvailable: true, windowWidth: 400, hardwareConcurrency: 16 });
    expect(result.tier).toBe("low");
    expect(result.forceFallback).toBe(true);
  });

  it("puts tablet widths in the mid tier", () => {
    const result = detectPerformanceTier({ webglAvailable: true, windowWidth: 900, hardwareConcurrency: 8 });
    expect(result.tier).toBe("mid");
    expect(result.forceFallback).toBe(false);
  });

  it("puts low hardwareConcurrency in the mid tier even on a wide viewport", () => {
    const result = detectPerformanceTier({ webglAvailable: true, windowWidth: 1600, hardwareConcurrency: 2 });
    expect(result.tier).toBe("mid");
  });

  it("gives capable desktops the high tier", () => {
    const result = detectPerformanceTier({ webglAvailable: true, windowWidth: 1600, hardwareConcurrency: 8 });
    expect(result.tier).toBe("high");
    expect(result.featureNodeCap).toBeGreaterThan(30);
  });
});

describe("usePrefersReducedMotion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reads the initial matchMedia state", () => {
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: true,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));

    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(true);
  });

  it("defaults to false when the preference is not set", () => {
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: false,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }));

    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);
  });
});
