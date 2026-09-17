/** Baseline ML — mirrors `backend/app/api/ml.py`. */

import { request } from "./http";
import type { CompareRequest, ComparisonResult, ModelResult, TaskTypesResponse, TrainRequest, ValidateTargetRequest, ValidateTargetResponse } from "./types";

function base(datasetId: string): string {
  return `/api/v1/datasets/${encodeURIComponent(datasetId)}/ml`;
}

export function getTaskTypes(): Promise<TaskTypesResponse> {
  return request<TaskTypesResponse>("/api/v1/ml/task-types");
}

export function validateTarget(datasetId: string, body: ValidateTargetRequest): Promise<ValidateTargetResponse> {
  return request<ValidateTargetResponse>(`${base(datasetId)}/validate-target`, { method: "POST", json: body });
}

export function trainModel(datasetId: string, body: TrainRequest): Promise<ModelResult> {
  return request<ModelResult>(`${base(datasetId)}/train`, { method: "POST", json: body });
}

export function compareModels(datasetId: string, body: CompareRequest): Promise<ComparisonResult> {
  return request<ComparisonResult>(`${base(datasetId)}/compare`, { method: "POST", json: body });
}
