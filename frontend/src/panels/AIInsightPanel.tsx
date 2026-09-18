import { Link } from "react-router-dom";

import { analyzeDatasetSummary } from "../api-client";
import type { AIAnalyzeResponse, AIStatusResponse, DatasetSummaryEvidence } from "../api-client";
import { Badge } from "../components/Badge";
import { ErrorState, LoadingSkeleton } from "../components/StatusStates";
import { useLazyAsync } from "../hooks/useAsync";
import { AIExplanationBlock, AIUnavailableNotice } from "./AIExplanationBlock";
import { EvidenceSources } from "./EvidenceSources";

/** AI Insights domain detail. Deliberately labeled "AI Interpretation," never "Computed
 * Result" (§20) — the secondary accent color (`tailwind.config.js`) and this label
 * together keep it visually and textually distinct from every deterministic panel. A
 * single representative capability (dataset summary) is offered inline; the full 5-
 * capability + Q&A experience remains the existing `/ai` tab (`features/ai/AiPage.tsx`) —
 * not duplicated here. */
export function AIInsightPanel({ datasetId, aiStatus }: { datasetId: string; aiStatus: AIStatusResponse | null }) {
  const summary = useLazyAsync(() => analyzeDatasetSummary(datasetId));
  const result: AIAnalyzeResponse<DatasetSummaryEvidence> | undefined = summary.status === "success" ? summary.data : undefined;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Badge tone={aiStatus?.available ? "good" : "neutral"}>{aiStatus?.available ? "Available" : "Unavailable"}</Badge>
        {aiStatus && <span className="font-mono text-xs text-slate-400">provider: {aiStatus.provider}</span>}
      </div>
      {aiStatus?.reason && <p className="text-xs text-slate-500">{aiStatus.reason}</p>}

      <button
        type="button"
        onClick={() => summary.run()}
        disabled={summary.status === "loading"}
        className="w-fit rounded-md border border-accent-secondary/30 px-3 py-1.5 text-xs font-medium text-accent-secondary transition hover:bg-accent-secondary/10 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {summary.status === "loading" ? "Thinking…" : "AI Interpretation — dataset summary"}
      </button>

      {summary.status === "error" && <ErrorState message={summary.message} />}
      {summary.status === "loading" && <LoadingSkeleton rows={3} />}
      {result && (
        <div>
          {result.available ? (
            <AIExplanationBlock explanation={result.ai_explanation} limitations={result.limitations} />
          ) : (
            <AIUnavailableNotice reason={result.reason} />
          )}
          <EvidenceSources sources={result.evidence_sources} />
        </div>
      )}

      <Link
        to={`/datasets/${datasetId}/ai`}
        className="mt-2 w-fit rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
      >
        Open full AI Insights tab (all capabilities + Q&A)
      </Link>
    </div>
  );
}
