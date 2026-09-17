/** Dataset ingestion — mirrors `backend/app/api/datasets.py`. */

import { request } from "./http";
import type { DatasetMetadata, DatasetSummary } from "./types";

export function uploadDataset(file: File): Promise<DatasetMetadata> {
  const formData = new FormData();
  formData.append("file", file);
  return request<DatasetMetadata>("/api/v1/datasets", { method: "POST", formData });
}

export function listDatasets(): Promise<DatasetSummary[]> {
  return request<DatasetSummary[]>("/api/v1/datasets");
}

export function getDataset(datasetId: string): Promise<DatasetMetadata> {
  return request<DatasetMetadata>(`/api/v1/datasets/${encodeURIComponent(datasetId)}`);
}
