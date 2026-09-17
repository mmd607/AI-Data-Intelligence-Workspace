/**
 * The ONLY module allowed to call the backend directly.
 *
 * Per 02_DOCS/ARCHITECTURE.md "Module Boundaries": "no component may call the backend
 * directly — all network access goes through a single typed API-client module." Every
 * later phase's data fetching extends this file (or sibling files in this directory),
 * never a raw `fetch` inside a component.
 */

import type { HealthResponse } from "./types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new ApiError(`Network error while calling ${path}`);
  }
  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}
