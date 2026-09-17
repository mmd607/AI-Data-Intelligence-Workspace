/** Grounded AI analytics — mirrors `backend/app/api/ai.py`. */

import { request } from "./http";
import type {
  AIAnalyzeRequest,
  AIAnalyzeResponse,
  AIQueryRequest,
  AIQueryResponse,
  AIStatusResponse,
  ColumnInsightEvidence,
  CorrelationExplanationEvidence,
  DatasetSummaryEvidence,
  MlExplanationEvidence,
  QualityExplanationEvidence,
} from "./types";

function base(datasetId: string): string {
  return `/api/v1/datasets/${encodeURIComponent(datasetId)}/ai`;
}

export function getAiStatus(): Promise<AIStatusResponse> {
  return request<AIStatusResponse>("/api/v1/ai/status");
}

/** Generic — prefer the capability-specific helpers below for a typed `computed` field. */
export function analyzeDataset<TComputed = Record<string, unknown>>(
  datasetId: string,
  body: AIAnalyzeRequest,
): Promise<AIAnalyzeResponse<TComputed>> {
  return request<AIAnalyzeResponse<TComputed>>(`${base(datasetId)}/analyze`, { method: "POST", json: body });
}

export function analyzeDatasetSummary(datasetId: string): Promise<AIAnalyzeResponse<DatasetSummaryEvidence>> {
  return analyzeDataset<DatasetSummaryEvidence>(datasetId, { capability: "dataset_summary" });
}

export function analyzeQuality(datasetId: string): Promise<AIAnalyzeResponse<QualityExplanationEvidence>> {
  return analyzeDataset<QualityExplanationEvidence>(datasetId, { capability: "quality_explanation" });
}

export function analyzeColumn(datasetId: string, columnName: string): Promise<AIAnalyzeResponse<ColumnInsightEvidence>> {
  return analyzeDataset<ColumnInsightEvidence>(datasetId, { capability: "column_insight", column_name: columnName });
}

export function analyzeCorrelation(datasetId: string): Promise<AIAnalyzeResponse<CorrelationExplanationEvidence>> {
  return analyzeDataset<CorrelationExplanationEvidence>(datasetId, { capability: "correlation_explanation" });
}

export function analyzeMlResult(
  datasetId: string,
  mlResult: AIAnalyzeRequest["ml_result"],
): Promise<AIAnalyzeResponse<MlExplanationEvidence>> {
  return analyzeDataset<MlExplanationEvidence>(datasetId, { capability: "ml_explanation", ml_result: mlResult });
}

export function queryDataset(datasetId: string, body: AIQueryRequest): Promise<AIQueryResponse> {
  return request<AIQueryResponse>(`${base(datasetId)}/query`, { method: "POST", json: body });
}
