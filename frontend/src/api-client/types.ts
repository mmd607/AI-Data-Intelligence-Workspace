/**
 * Types mirroring the backend's Pydantic response models exactly — transcribed from the
 * actual schema files (`backend/app/{ingestion,profiling,ml,ai}/schemas.py`), not
 * invented, per `01_PHASES/PHASE_06_API_FRONTEND_INTEGRATION/PHASE_PROMPT.md` ("Do not
 * invent API contracts. Use the actual FastAPI OpenAPI/schema implementation.").
 *
 * A Python `datetime` field is serialized by Pydantic as an ISO-8601 string, so every
 * such field here is typed `string`, never `Date`.
 */

// ---------------------------------------------------------------------------
// Shared error envelope
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  code: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Ingestion (backend/app/ingestion/schemas.py)
// ---------------------------------------------------------------------------

export interface ColumnInfo {
  name: string;
  dtype: string;
}

export interface DatasetMetadata {
  id: string;
  original_filename: string;
  uploaded_at: string;
  size_bytes: number;
  row_count: number;
  column_count: number;
  columns: ColumnInfo[];
  missing_value_count: number;
  duplicate_row_count: number;
}

export interface DatasetSummary {
  id: string;
  original_filename: string;
  uploaded_at: string;
  size_bytes: number;
  row_count: number;
  column_count: number;
}

// ---------------------------------------------------------------------------
// Profiling (backend/app/profiling/schemas.py)
// ---------------------------------------------------------------------------

export type SemanticType = "numeric" | "boolean" | "datetime" | "categorical" | "text" | "unknown";

export interface NumericColumnStats {
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  std: number | null;
  q1: number | null;
  q3: number | null;
  iqr: number | null;
  zero_count: number;
  negative_count: number;
  infinite_count: number;
}

export interface ValueFrequency {
  value: string;
  count: number;
  percentage: number;
}

export interface CategoricalColumnStats {
  cardinality: number;
  top_values: ValueFrequency[];
  rare_value_count: number;
}

export interface DatetimeColumnStats {
  min_date: string | null;
  max_date: string | null;
  date_range_days: number | null;
  missing_count: number;
  unparseable_count: number;
}

/** A raw sample value as returned by pandas — never assume it's always a string. */
export type SampleValue = string | number | boolean | null;

export interface ColumnProfile {
  name: string;
  pandas_dtype: string;
  semantic_type: SemanticType;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  sample_values: SampleValue[];
  numeric_stats: NumericColumnStats | null;
  categorical_stats: CategoricalColumnStats | null;
  datetime_stats: DatetimeColumnStats | null;
}

export interface MissingValueSummary {
  total_missing_cells: number;
  missing_percentage: number;
  columns_with_missing: number;
}

export interface DatasetProfile {
  dataset_id: string;
  row_count: number;
  column_count: number;
  memory_usage_bytes: number;
  duplicate_row_count: number;
  duplicate_row_percentage: number;
  missing: MissingValueSummary;
  columns: ColumnProfile[];
  generated_at: string;
}

export type QualitySeverity = "info" | "warning" | "critical";

export interface QualityFinding {
  code: string;
  severity: QualitySeverity;
  column: string | null;
  message: string;
  metric: number | null;
  details: Record<string, unknown>;
}

export interface QualitySummary {
  dataset_id: string;
  findings: QualityFinding[];
  finding_count: number;
  generated_at: string;
}

export interface CorrelationPair {
  column_a: string;
  column_b: string;
  coefficient: number;
  observations: number;
}

/** `status` is `"computed"` or `"insufficient_data"` — never silently empty. */
export type CorrelationStatus = "computed" | "insufficient_data";

export interface CorrelationResult {
  dataset_id: string;
  method: string;
  minimum_observations: number;
  eligible_columns: string[];
  pairs: CorrelationPair[];
  status: CorrelationStatus;
  message: string | null;
  generated_at: string;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface ColumnDistribution {
  column: string;
  bin_count: number;
  bins: HistogramBin[];
  min: number;
  max: number;
}

export interface DistributionResult {
  dataset_id: string;
  columns: ColumnDistribution[];
  skipped_columns: string[];
  generated_at: string;
}

// ---------------------------------------------------------------------------
// ML (backend/app/ml/schemas.py)
// ---------------------------------------------------------------------------

export type TaskType = "binary_classification" | "multiclass_classification" | "regression";

export type ModelName =
  | "logistic_regression"
  | "random_forest_classifier"
  | "linear_regression"
  | "ridge_regression"
  | "random_forest_regressor";

export interface TaskTypeInfo {
  task_type: TaskType;
  label: string;
  description: string;
  supported_models: ModelName[];
}

export interface TaskTypesResponse {
  task_types: TaskTypeInfo[];
}

export interface ObservedTargetFacts {
  row_count: number;
  non_null_count: number;
  null_count: number;
  unique_count: number;
  pandas_dtype: string;
  semantic_type: SemanticType;
}

export interface TaskSuitability {
  task_type: TaskType;
  suitable: boolean;
  reason: string;
}

export interface ValidateTargetRequest {
  target_column: string;
}

export interface ValidateTargetResponse {
  dataset_id: string;
  target_column: string;
  observed: ObservedTargetFacts;
  suitable_tasks: TaskSuitability[];
  suggested_task: TaskType | null;
  is_suggestion: boolean;
}

export interface TrainRequest {
  target_column: string;
  task_type: TaskType;
  model_name: ModelName;
  test_size?: number;
  random_state?: number;
}

export interface CompareRequest {
  target_column: string;
  task_type: TaskType;
  model_names: ModelName[];
  test_size?: number;
  random_state?: number;
}

export interface ExcludedColumn {
  column: string;
  reason: string;
}

export interface PreprocessingSummary {
  numeric_features: string[];
  categorical_features: string[];
  numeric_transform: string;
  categorical_transform: string;
}

export interface TrainingConfig {
  test_size: number;
  random_state: number;
  stratified: boolean;
}

export interface ConfusionMatrixResult {
  labels: string[];
  matrix: number[][];
}

export interface ModelResult {
  dataset_id: string;
  target_column: string;
  task_type: TaskType;
  feature_columns: string[];
  excluded_columns: ExcludedColumn[];
  preprocessing: PreprocessingSummary;
  model_name: ModelName;
  training_config: TrainingConfig;
  train_size: number;
  test_size_actual: number;
  metrics: Record<string, number>;
  unavailable_metrics: Record<string, string>;
  confusion_matrix: ConfusionMatrixResult | null;
  warnings: string[];
  limitations: string[];
  generated_at: string;
}

export interface ComparisonResult {
  dataset_id: string;
  target_column: string;
  task_type: TaskType;
  results: ModelResult[];
  generated_at: string;
}

// ---------------------------------------------------------------------------
// AI (backend/app/ai/schemas.py)
// ---------------------------------------------------------------------------

export type AICapability =
  | "dataset_summary"
  | "quality_explanation"
  | "column_insight"
  | "correlation_explanation"
  | "ml_explanation";

export type QuestionCategory =
  | "deterministic_lookup"
  | "explanation"
  | "analytical_interpretation"
  | "unsupported";

export interface AIStatusResponse {
  enabled: boolean;
  provider: string;
  model: string | null;
  available: boolean;
  reason: string | null;
}

export interface AIAnalyzeRequest {
  capability: AICapability;
  column_name?: string;
  /** Required for `ml_explanation` — the caller supplies the already-computed
   * Phase 04 `ModelResult` directly (no model-persistence layer exists, ADR-013). */
  ml_result?: ModelResult;
}

export interface AIQueryRequest {
  question: string;
  ml_result?: ModelResult;
}

export interface AIExplanation {
  source: "ai_generated";
  provider: string;
  model: string | null;
  text: string;
  generated_at: string;
}

/** The deterministic evidence for the `dataset_summary` capability, exactly as built by
 * `backend/app/ai/evidence.py::build_dataset_summary_evidence`. */
export interface DatasetSummaryEvidence {
  dataset_id: string;
  row_count: number;
  column_count: number;
  missing_percentage: number;
  duplicate_row_percentage: number;
  quality_finding_count: number;
  quality_severity_counts: Record<string, number>;
  columns: Array<{
    name: string;
    semantic_type: SemanticType;
    null_percentage: number;
    unique_percentage: number;
  }>;
}

export interface QualityExplanationEvidence {
  dataset_id: string;
  finding_count: number;
  findings: Array<{
    code: string;
    severity: QualitySeverity;
    column: string | null;
    message: string;
    metric: number | null;
  }>;
}

export interface ColumnInsightEvidence {
  dataset_id: string;
  column_name: string;
  pandas_dtype: string;
  semantic_type: SemanticType;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  sample_values: SampleValue[];
  numeric_stats: NumericColumnStats | null;
  categorical_stats: CategoricalColumnStats | null;
  datetime_stats: DatetimeColumnStats | null;
}

export interface CorrelationExplanationEvidence {
  dataset_id: string;
  method: string;
  status: CorrelationStatus;
  message: string | null;
  pairs: CorrelationPair[];
}

export interface MlExplanationEvidence {
  task_type: TaskType;
  target_column: string;
  model_name: ModelName;
  feature_columns: string[];
  train_size: number;
  test_size_actual: number;
  metrics: Record<string, number>;
  unavailable_metrics: Record<string, string>;
  warnings: string[];
  limitations: string[];
}

/** The evidence shape for `POST .../ai/query` — `context` is only present when the
 * question routed to `explanation`/`analytical_interpretation` (see `service.py`). */
export interface QueryEvidence {
  dataset_id: string;
  question: string;
  question_category: QuestionCategory;
  resolved_answer: string | null;
  context?: DatasetSummaryEvidence;
}

export interface AIAnalyzeResponse<TComputed = Record<string, unknown>> {
  dataset_id: string;
  capability: AICapability;
  computed: TComputed;
  evidence_sources: string[];
  ai_explanation: AIExplanation | null;
  grounded: boolean;
  limitations: string[];
  available: boolean;
  reason: string | null;
}

export interface AIQueryResponse {
  dataset_id: string;
  question: string;
  question_category: QuestionCategory;
  computed: QueryEvidence;
  evidence_sources: string[];
  ai_explanation: AIExplanation | null;
  grounded: boolean;
  limitations: string[];
  available: boolean;
  reason: string | null;
}

// ---------------------------------------------------------------------------
// Health (backend/app/api/health.py)
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  timestamp: string;
}
