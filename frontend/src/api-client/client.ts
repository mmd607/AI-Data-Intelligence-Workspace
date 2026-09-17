/**
 * Health check — kept as its own top-level export for backward compatibility with
 * existing imports (`./api-client/client`). See `index.ts` for the full typed surface
 * added in Phase 06 (`datasets.ts`, `profiling.ts`, `ml.ts`, `ai.ts`).
 */

export { ApiError } from "./http";
import { request } from "./http";
import type { HealthResponse } from "./types";

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}
