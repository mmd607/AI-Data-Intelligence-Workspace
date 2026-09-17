/**
 * Barrel export — the single import surface every component/hook should use
 * (`import { ... } from "../api-client"`), per 02_DOCS/ARCHITECTURE.md "Module
 * Boundaries".
 */

export { ApiError } from "./http";
export { getHealth } from "./client";
export { getDataset, listDatasets, uploadDataset } from "./datasets";
export { getColumnProfile, getCorrelation, getDatasetProfile, getDistribution, getQualitySummary } from "./profiling";
export { compareModels, getTaskTypes, trainModel, validateTarget } from "./ml";
export {
  analyzeColumn,
  analyzeCorrelation,
  analyzeDataset,
  analyzeDatasetSummary,
  analyzeMlResult,
  analyzeQuality,
  getAiStatus,
  queryDataset,
} from "./ai";
export * from "./types";
