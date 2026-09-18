import { useState } from "react";

import { analyzeColumn } from "../api-client";
import type { AIAnalyzeResponse, ColumnInsightEvidence, ColumnProfile } from "../api-client";
import { Badge } from "../components/Badge";
import { ErrorState, LoadingSkeleton } from "../components/StatusStates";
import { StatValue } from "../components/StatValue";
import { useLazyAsync } from "../hooks/useAsync";
import { FrequencyList } from "../viz/FrequencyBar";
import { AIExplanationBlock, AIUnavailableNotice } from "./AIExplanationBlock";
import { EvidenceSources } from "./EvidenceSources";

/** Feature detail (`02_DOCS/UI_UX_SPEC.md` §14) — `column` is the real `ColumnProfile`
 * `UniversePage` already has from the one `getDatasetProfile` call; nothing is re-fetched
 * here except the optional, explicitly-triggered AI column insight. */
export function FeaturePanel({
  datasetId,
  column,
  hasQualityWarning,
  hasQualityCritical,
}: {
  datasetId: string;
  column: ColumnProfile;
  hasQualityWarning: boolean;
  hasQualityCritical: boolean;
}) {
  const [insight, setInsight] = useState<AIAnalyzeResponse<ColumnInsightEvidence> | null>(null);
  const ai = useLazyAsync(() => analyzeColumn(datasetId, column.name));

  async function runInsight() {
    const result = await ai.run();
    if (result) setInsight(result);
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="neutral">{column.semantic_type}</Badge>
        <span className="font-mono text-xs text-slate-500">{column.pandas_dtype}</span>
        {hasQualityCritical && <Badge tone="critical">quality: critical</Badge>}
        {!hasQualityCritical && hasQualityWarning && <Badge tone="warning">quality: warning</Badge>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <StatValue label="Missing" value={column.null_count} unit={`(${column.null_percentage}%)`} />
        <StatValue label="Unique" value={column.unique_count} unit={`(${column.unique_percentage}%)`} />
      </div>

      {column.numeric_stats && (
        // Deliberately grid-cols-2, not a `sm:`/`md:` viewport breakpoint: this panel is a
        // fixed-width slide-in (`panels/DetailPanel.tsx`) whose own width never tracks the
        // viewport, so a viewport breakpoint here previously caused 3 cramped columns (and
        // visually overlapping long numeric values) on any wide screen regardless of how
        // narrow the panel itself actually is.
        <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
          <StatValue label="Min" value={column.numeric_stats.min} />
          <StatValue label="Max" value={column.numeric_stats.max} />
          <StatValue label="Mean" value={column.numeric_stats.mean} />
          <StatValue label="Median" value={column.numeric_stats.median} />
          <StatValue label="Std dev" value={column.numeric_stats.std} />
          <StatValue label="IQR" value={column.numeric_stats.iqr} />
        </div>
      )}

      {column.categorical_stats && (
        <div className="border-t border-white/5 pt-4">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Top values</p>
          <FrequencyList values={column.categorical_stats.top_values} />
        </div>
      )}

      {column.datetime_stats && (
        <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-4">
          <StatValue label="Earliest" value={column.datetime_stats.min_date} />
          <StatValue label="Latest" value={column.datetime_stats.max_date} />
          <StatValue label="Range" value={column.datetime_stats.date_range_days} unit="days" />
        </div>
      )}

      <div className="border-t border-white/5 pt-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Sample values</p>
        <p className="font-mono text-xs text-slate-400">
          {column.sample_values.map((v) => (v === null ? "∅" : String(v))).join(", ") || "—"}
        </p>
      </div>

      <div className="border-t border-white/5 pt-4">
        <button
          type="button"
          onClick={runInsight}
          disabled={ai.status === "loading"}
          className="rounded-md border border-accent-secondary/30 px-3 py-1.5 text-xs font-medium text-accent-secondary transition hover:bg-accent-secondary/10 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {ai.status === "loading" ? "Thinking…" : "AI column insight"}
        </button>
        {ai.status === "error" && <ErrorState message={ai.message} />}
        {ai.status === "loading" && <LoadingSkeleton rows={2} />}
        {insight && (
          <>
            {insight.available ? (
              <AIExplanationBlock explanation={insight.ai_explanation} limitations={insight.limitations} />
            ) : (
              <AIUnavailableNotice reason={insight.reason} />
            )}
            <EvidenceSources sources={insight.evidence_sources} />
          </>
        )}
      </div>
    </div>
  );
}
