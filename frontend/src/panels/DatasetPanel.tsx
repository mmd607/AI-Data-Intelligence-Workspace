import { Link } from "react-router-dom";

import type { AIStatusResponse, CorrelationResult, DatasetMetadata, DatasetProfile, ModelResult, QualitySummary } from "../api-client";
import { Badge } from "../components/Badge";
import { StatValue } from "../components/StatValue";

/** Dataset overview (`02_DOCS/UI_UX_SPEC.md` §16) — every field is passed down from data
 * `UniversePage` already fetched once for the graph itself; nothing is re-fetched or
 * recomputed here. */
export function DatasetPanel({
  dataset,
  profile,
  quality,
  correlation,
  mlResult,
  aiStatus,
}: {
  dataset: DatasetMetadata;
  profile: DatasetProfile | null;
  quality: QualitySummary | null;
  correlation: CorrelationResult | null;
  mlResult: ModelResult | null;
  aiStatus: AIStatusResponse | null;
}) {
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-4">
        <StatValue label="Rows" value={dataset.row_count} />
        <StatValue label="Columns" value={dataset.column_count} />
        <StatValue label="Duplicate rows" value={dataset.duplicate_row_count} />
        <StatValue label="Size" value={(dataset.size_bytes / 1024).toFixed(1)} unit="KB" />
        {profile && <StatValue label="Missing cells" value={profile.missing.total_missing_cells} unit={`(${profile.missing.missing_percentage}%)`} />}
      </div>

      <div className="flex flex-col gap-2 border-t border-white/5 pt-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Quality</p>
        {quality ? (
          <Badge tone={quality.finding_count === 0 ? "good" : "warning"}>
            {quality.finding_count === 0 ? "No findings" : `${quality.finding_count} finding(s)`}
          </Badge>
        ) : (
          <Badge tone="neutral">Not loaded</Badge>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t border-white/5 pt-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Analytics</p>
        {correlation ? (
          <Badge tone={correlation.status === "computed" ? "good" : "neutral"}>
            {correlation.status === "computed" ? `${correlation.pairs.length} correlation pair(s)` : "Insufficient data"}
          </Badge>
        ) : (
          <Badge tone="neutral">Not loaded</Badge>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t border-white/5 pt-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">ML</p>
        <Badge tone={mlResult ? "good" : "neutral"}>{mlResult ? `${mlResult.model_name} trained` : "No model trained"}</Badge>
      </div>

      <div className="flex flex-col gap-2 border-t border-white/5 pt-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">AI Insights</p>
        <Badge tone={aiStatus?.available ? "good" : "neutral"}>
          {aiStatus ? (aiStatus.available ? `${aiStatus.provider} available` : (aiStatus.reason ?? "Unavailable")) : "Not loaded"}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2 border-t border-white/5 pt-4">
        <Link to={`/datasets/${dataset.id}`} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
          Overview
        </Link>
        <Link to={`/datasets/${dataset.id}/quality`} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
          Quality
        </Link>
        <Link to={`/datasets/${dataset.id}/analytics`} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
          Analytics
        </Link>
        <Link to={`/datasets/${dataset.id}/ml`} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
          ML
        </Link>
        <Link to={`/datasets/${dataset.id}/ai`} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
          AI Insights
        </Link>
      </div>
    </div>
  );
}
