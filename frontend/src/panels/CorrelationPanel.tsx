import type { CorrelationResult } from "../api-client";
import { EmptyState } from "../components/StatusStates";
import { CorrelationBar } from "../viz/CorrelationBar";

/** Analytics domain detail — the exact pairs/coefficients the 3D Analytics ring renders
 * as edges, in precise 2D form ("3D is for spatial context, 2D is for precise
 * information," per this phase's own brief). Presentational only, same `correlation`
 * `UniversePage` already fetched. */
export function CorrelationPanel({ correlation }: { correlation: CorrelationResult | null }) {
  if (!correlation) return <EmptyState title="Not loaded yet" hint="Correlation data is still loading." />;
  if (correlation.status === "insufficient_data") {
    return <EmptyState title="Not enough data for correlation" hint={correlation.message ?? undefined} />;
  }
  if (correlation.pairs.length === 0) {
    return <EmptyState title="No correlation pairs computed" />;
  }

  return (
    <div className="flex flex-col gap-3">
      {[...correlation.pairs]
        .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
        .map((pair) => (
          <div key={`${pair.column_a}-${pair.column_b}`} className="flex flex-col gap-1">
            <p className="font-mono text-xs text-slate-400">
              {pair.column_a} × {pair.column_b} <span className="text-slate-600">({pair.observations} observations)</span>
            </p>
            <CorrelationBar coefficient={pair.coefficient} />
          </div>
        ))}
      <p className="mt-2 border-t border-white/5 pt-3 text-xs text-slate-500">
        A correlation, however strong, describes a statistical association only — it does not establish causation.
      </p>
    </div>
  );
}
