/** Dataset profiling/quality/correlation/distribution — mirrors `backend/app/api/profile.py`. */

import { request } from "./http";
import type { ColumnProfile, CorrelationResult, DatasetProfile, DistributionResult, QualitySummary } from "./types";

function base(datasetId: string): string {
  return `/api/v1/datasets/${encodeURIComponent(datasetId)}`;
}

export function getDatasetProfile(datasetId: string): Promise<DatasetProfile> {
  return request<DatasetProfile>(`${base(datasetId)}/profile`);
}

export function getQualitySummary(datasetId: string): Promise<QualitySummary> {
  return request<QualitySummary>(`${base(datasetId)}/quality`);
}

export function getColumnProfile(datasetId: string, columnName: string): Promise<ColumnProfile> {
  return request<ColumnProfile>(`${base(datasetId)}/columns/${encodeURIComponent(columnName)}`);
}

export function getCorrelation(datasetId: string): Promise<CorrelationResult> {
  return request<CorrelationResult>(`${base(datasetId)}/correlation`);
}

export function getDistribution(datasetId: string): Promise<DistributionResult> {
  return request<DistributionResult>(`${base(datasetId)}/distribution`);
}
