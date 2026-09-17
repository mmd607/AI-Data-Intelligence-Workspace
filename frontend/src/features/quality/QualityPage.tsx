import { getQualitySummary } from "../../api-client";
import { Badge } from "../../components/Badge";
import { severityToTone } from "../../components/severity";
import { Card } from "../../components/Card";
import { EmptyState, ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { useAsync } from "../../hooks/useAsync";
import { useWorkspaceDataset } from "../workspace/useWorkspaceDataset";

export function QualityPage() {
  const dataset = useWorkspaceDataset();
  const quality = useAsync(() => getQualitySummary(dataset.id), [dataset.id]);

  return (
    <Card
      title="Data quality"
      description="Rule-based findings computed deterministically from the dataset — missing values, duplicates, constant/near-constant columns, high-cardinality categoricals, mixed types, and more."
    >
      {quality.status === "loading" && <LoadingSkeleton rows={4} />}
      {quality.status === "error" && <ErrorState message={quality.message} onRetry={quality.refetch} />}
      {quality.status === "success" && quality.data.findings.length === 0 && (
        <EmptyState title="No data-quality findings" hint="This dataset passed every deterministic quality check." />
      )}
      {quality.status === "success" && quality.data.findings.length > 0 && (
        <ul className="flex flex-col divide-y divide-white/5">
          {quality.data.findings.map((finding, i) => (
            <li key={`${finding.code}-${i}`} className="flex items-start justify-between gap-4 py-3">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <Badge tone={severityToTone(finding.severity)}>{finding.severity}</Badge>
                  <span className="font-mono text-xs text-slate-500">{finding.code}</span>
                  {finding.column && <span className="font-mono text-xs text-slate-400">· {finding.column}</span>}
                </div>
                <p className="text-sm text-slate-300">{finding.message}</p>
              </div>
              {finding.metric !== null && (
                <span className="shrink-0 font-mono text-sm text-slate-300">{finding.metric}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
