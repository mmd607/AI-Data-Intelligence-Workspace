import { useState } from "react";

import {
  analyzeColumn,
  analyzeCorrelation,
  analyzeDatasetSummary,
  analyzeMlResult,
  analyzeQuality,
  getAiStatus,
} from "../../api-client";
import type {
  AIAnalyzeResponse,
  AICapability,
  ColumnInsightEvidence,
  CorrelationExplanationEvidence,
  DatasetSummaryEvidence,
  MlExplanationEvidence,
  QualityExplanationEvidence,
} from "../../api-client";
import { Badge } from "../../components/Badge";
import { severityToTone } from "../../components/severity";
import { Card } from "../../components/Card";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { StatValue } from "../../components/StatValue";
import { useAsync } from "../../hooks/useAsync";
import { useDatasetSession } from "../../state/useDatasetSession";
import { useWorkspaceDataset } from "../workspace/useWorkspaceDataset";
import { CorrelationBar } from "../../viz/CorrelationBar";
import { AIExplanationBlock, AIUnavailableNotice } from "../../panels/AIExplanationBlock";
import { EvidenceSources } from "../../panels/EvidenceSources";
import { QaPanel } from "./QaPanel";

type ActiveResult =
  | { capability: "dataset_summary"; response: AIAnalyzeResponse<DatasetSummaryEvidence> }
  | { capability: "quality_explanation"; response: AIAnalyzeResponse<QualityExplanationEvidence> }
  | { capability: "column_insight"; response: AIAnalyzeResponse<ColumnInsightEvidence> }
  | { capability: "correlation_explanation"; response: AIAnalyzeResponse<CorrelationExplanationEvidence> }
  | { capability: "ml_explanation"; response: AIAnalyzeResponse<MlExplanationEvidence> };

const CAPABILITY_LABELS: Record<AICapability, string> = {
  dataset_summary: "Dataset summary",
  quality_explanation: "Data quality",
  column_insight: "Column insight",
  correlation_explanation: "Correlation",
  ml_explanation: "ML result",
};

function ComputedGrid({ computed }: { computed: Record<string, number | string | null> }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {Object.entries(computed).map(([key, value]) => (
        <StatValue key={key} label={key.replace(/_/g, " ")} value={value} />
      ))}
    </div>
  );
}

function RenderedComputed({ result }: { result: ActiveResult }) {
  switch (result.capability) {
    case "dataset_summary": {
      const c = result.response.computed;
      return (
        <div className="flex flex-col gap-4">
          <ComputedGrid
            computed={{
              row_count: c.row_count,
              column_count: c.column_count,
              missing_percentage: c.missing_percentage,
              duplicate_row_percentage: c.duplicate_row_percentage,
              quality_findings: c.quality_finding_count,
            }}
          />
          <ul className="flex flex-col gap-1 text-xs text-slate-400">
            {c.columns.map((col) => (
              <li key={col.name} className="font-mono">
                {col.name} · {col.semantic_type} · {col.null_percentage}% null
              </li>
            ))}
          </ul>
        </div>
      );
    }
    case "quality_explanation": {
      const c = result.response.computed;
      if (c.findings.length === 0) return <p className="text-sm text-slate-400">No findings reported.</p>;
      return (
        <ul className="flex flex-col divide-y divide-white/5">
          {c.findings.map((f, i) => (
            <li key={`${f.code}-${i}`} className="flex items-center gap-2 py-2">
              <Badge tone={severityToTone(f.severity)}>{f.severity}</Badge>
              <span className="text-sm text-slate-300">{f.message}</span>
            </li>
          ))}
        </ul>
      );
    }
    case "column_insight": {
      const c = result.response.computed;
      return (
        <div className="flex flex-col gap-4">
          <ComputedGrid
            computed={{
              column: c.column_name,
              semantic_type: c.semantic_type,
              null_percentage: c.null_percentage,
              unique_percentage: c.unique_percentage,
            }}
          />
          {c.numeric_stats && (
            <ComputedGrid
              computed={{
                min: c.numeric_stats.min,
                max: c.numeric_stats.max,
                mean: c.numeric_stats.mean,
                std: c.numeric_stats.std,
              }}
            />
          )}
        </div>
      );
    }
    case "correlation_explanation": {
      const c = result.response.computed;
      if (c.pairs.length === 0) return <p className="text-sm text-slate-400">No correlation pairs available.</p>;
      return (
        <div className="flex flex-col gap-3">
          {c.pairs.map((pair) => (
            <div key={`${pair.column_a}-${pair.column_b}`} className="flex flex-col gap-1">
              <p className="font-mono text-xs text-slate-400">
                {pair.column_a} × {pair.column_b}
              </p>
              <CorrelationBar coefficient={pair.coefficient} />
            </div>
          ))}
        </div>
      );
    }
    case "ml_explanation": {
      const c = result.response.computed;
      return <ComputedGrid computed={c.metrics} />;
    }
  }
}

export function AiPage() {
  const dataset = useWorkspaceDataset();
  const { lastMlResult } = useDatasetSession();
  const status = useAsync(getAiStatus, []);

  const [result, setResult] = useState<ActiveResult | null>(null);
  const [columnName, setColumnName] = useState(dataset.columns[0]?.name ?? "");
  const [loadingCapability, setLoadingCapability] = useState<AICapability | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(capability: AICapability) {
    setLoadingCapability(capability);
    setError(null);
    try {
      switch (capability) {
        case "dataset_summary":
          setResult({ capability, response: await analyzeDatasetSummary(dataset.id) });
          break;
        case "quality_explanation":
          setResult({ capability, response: await analyzeQuality(dataset.id) });
          break;
        case "column_insight":
          setResult({ capability, response: await analyzeColumn(dataset.id, columnName) });
          break;
        case "correlation_explanation":
          setResult({ capability, response: await analyzeCorrelation(dataset.id) });
          break;
        case "ml_explanation":
          if (!lastMlResult) return;
          setResult({ capability, response: await analyzeMlResult(dataset.id, lastMlResult) });
          break;
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "The AI request failed.");
    } finally {
      setLoadingCapability(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card title="AI status">
        {status.status === "loading" && <LoadingSkeleton rows={1} />}
        {status.status === "error" && <ErrorState message={status.message} onRetry={status.refetch} />}
        {status.status === "success" && (
          <div className="flex items-center gap-3">
            <Badge tone={status.data.available ? "good" : "neutral"}>
              {status.data.available ? "Available" : "Unavailable"}
            </Badge>
            <span className="font-mono text-xs text-slate-400">provider: {status.data.provider}</span>
            {status.data.reason && <span className="text-xs text-slate-500">{status.data.reason}</span>}
          </div>
        )}
      </Card>

      <Card title="Grounded analysis" description="Deterministic evidence, computed first — the AI layer only ever narrates it.">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            {(Object.keys(CAPABILITY_LABELS) as AICapability[]).map((capability) => (
              <button
                key={capability}
                type="button"
                onClick={() => run(capability)}
                disabled={loadingCapability !== null || (capability === "ml_explanation" && !lastMlResult)}
                className="rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-30"
                title={capability === "ml_explanation" && !lastMlResult ? "Train a baseline model first" : undefined}
              >
                {loadingCapability === capability ? "Loading…" : CAPABILITY_LABELS[capability]}
              </button>
            ))}
            <select
              value={columnName}
              onChange={(e) => setColumnName(e.target.value)}
              className="rounded-md border border-white/10 bg-surface px-2 py-1.5 text-xs text-slate-300"
            >
              {dataset.columns.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {error && <ErrorState message={error} />}
          {loadingCapability && <LoadingSkeleton rows={3} />}

          {!loadingCapability && result && (
            <div>
              <RenderedComputed result={result} />
              {result.response.available ? (
                <AIExplanationBlock explanation={result.response.ai_explanation} limitations={result.response.limitations} />
              ) : (
                <AIUnavailableNotice reason={result.response.reason} />
              )}
              <EvidenceSources sources={result.response.evidence_sources} />
            </div>
          )}
        </div>
      </Card>

      <QaPanel datasetId={dataset.id} />
    </div>
  );
}
