import { getCorrelation, getDistribution } from "../../api-client";
import { Card } from "../../components/Card";
import { EmptyState, ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { useAsync } from "../../hooks/useAsync";
import { useWorkspaceDataset } from "../workspace/useWorkspaceDataset";
import { CorrelationBar } from "../../viz/CorrelationBar";
import { Histogram } from "../../viz/Histogram";

function DistributionsSection() {
  const dataset = useWorkspaceDataset();
  const distribution = useAsync(() => getDistribution(dataset.id), [dataset.id]);

  return (
    <Card
      title="Distributions"
      description="Histograms for numeric columns, binned by the backend (numpy.histogram) — never recomputed client-side."
    >
      {distribution.status === "loading" && <LoadingSkeleton rows={4} />}
      {distribution.status === "error" && <ErrorState message={distribution.message} onRetry={distribution.refetch} />}
      {distribution.status === "success" && distribution.data.columns.length === 0 && (
        <EmptyState
          title="No numeric columns to plot"
          hint="Distributions are only computed for numeric columns with finite, non-identical values."
        />
      )}
      {distribution.status === "success" && distribution.data.columns.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {distribution.data.columns.map((col) => (
            <div key={col.column} className="flex flex-col gap-2">
              <p className="font-mono text-sm text-slate-300">{col.column}</p>
              <Histogram bins={col.bins} />
              <p className="font-mono text-xs text-slate-500">
                {col.min} – {col.max}
              </p>
            </div>
          ))}
        </div>
      )}
      {distribution.status === "success" && distribution.data.skipped_columns.length > 0 && (
        <p className="mt-4 border-t border-white/5 pt-3 text-xs text-slate-500">
          Skipped (non-numeric, no finite values, or a single repeated value):{" "}
          {distribution.data.skipped_columns.join(", ")}
        </p>
      )}
    </Card>
  );
}

function CorrelationSection() {
  const dataset = useWorkspaceDataset();
  const correlation = useAsync(() => getCorrelation(dataset.id), [dataset.id]);

  return (
    <Card
      title="Correlation"
      description="Pairwise Pearson correlation between numeric columns. Correlation does not establish causation."
    >
      {correlation.status === "loading" && <LoadingSkeleton rows={3} />}
      {correlation.status === "error" && <ErrorState message={correlation.message} onRetry={correlation.refetch} />}
      {correlation.status === "success" && correlation.data.status === "insufficient_data" && (
        <EmptyState title="Not enough data for correlation" hint={correlation.data.message ?? undefined} />
      )}
      {correlation.status === "success" && correlation.data.status === "computed" && correlation.data.pairs.length === 0 && (
        <EmptyState title="No correlation pairs computed" />
      )}
      {correlation.status === "success" && correlation.data.pairs.length > 0 && (
        <div className="flex flex-col gap-3">
          {[...correlation.data.pairs]
            .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
            .map((pair) => (
              <div key={`${pair.column_a}-${pair.column_b}`} className="flex flex-col gap-1">
                <p className="font-mono text-xs text-slate-400">
                  {pair.column_a} × {pair.column_b}{" "}
                  <span className="text-slate-600">({pair.observations} observations)</span>
                </p>
                <CorrelationBar coefficient={pair.coefficient} />
              </div>
            ))}
          <p className="mt-2 border-t border-white/5 pt-3 text-xs text-slate-500">
            A correlation, however strong, describes a statistical association only — it does not establish
            causation.
          </p>
        </div>
      )}
    </Card>
  );
}

export function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-6">
      <DistributionsSection />
      <CorrelationSection />
    </div>
  );
}
