import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getHealth } from "./client";

describe("api-client/client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the parsed health payload on success", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "ok",
          service: "svc",
          environment: "development",
          timestamp: "2026-09-17T00:00:00Z",
        }),
        { status: 200 },
      ),
    );

    const health = await getHealth();
    expect(health.status).toBe("ok");
    expect(health.environment).toBe("development");
  });

  it("throws ApiError with the response status on a non-OK response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("nope", { status: 503 }));

    await expect(getHealth()).rejects.toBeInstanceOf(ApiError);
    await expect(getHealth()).rejects.toMatchObject({ status: 503 });
  });

  it("throws ApiError on a network failure", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(getHealth()).rejects.toBeInstanceOf(ApiError);
  });
});
