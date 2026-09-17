/**
 * Types mirroring the backend's Pydantic response models.
 *
 * Phase 06 replaces this hand-maintained file with types generated/validated from the
 * backend's OpenAPI schema (see 02_DOCS/ARCHITECTURE.md "API Contract Philosophy"). Phase
 * 01 only needs the health check shape.
 */

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  timestamp: string;
}
