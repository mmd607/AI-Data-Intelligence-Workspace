import { Link } from "react-router-dom";

import type { ModelResult } from "../api-client";
import { EmptyState } from "../components/StatusStates";
import { StatValue } from "../components/StatValue";

/** ML domain detail — `mlResult` is the session's last-trained `ModelResult`
 * (`state/DatasetSessionContext.tsx`), the same one `UniversePage` already reads for the
 * graph; no model persistence layer exists (ADR-013), so this is the only real result to
 * show. */
export function MLPanel({ datasetId, mlResult }: { datasetId: string; mlResult: ModelResult | null }) {
  if (!mlResult) {
    return (
      <div className="flex flex-col gap-3">
        <EmptyState title="No model trained yet" hint="Train a baseline model to see it here." />
        <Link
          to={`/datasets/${datasetId}/ml`}
          className="w-fit rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
        >
          Open ML tab
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="font-mono text-sm text-slate-300">
        {mlResult.model_name} · {mlResult.task_type} · target: {mlResult.target_column}
      </p>
      <div className="grid grid-cols-2 gap-4">
        <StatValue label="Train rows" value={mlResult.train_size} />
        <StatValue label="Test rows" value={mlResult.test_size_actual} />
        <StatValue label="Features" value={mlResult.feature_columns.length} />
        <StatValue label="Excluded" value={mlResult.excluded_columns.length} />
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Metrics</p>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(mlResult.metrics).map(([name, value]) => (
            <StatValue key={name} label={name} value={value} />
          ))}
        </div>
      </div>
      {(mlResult.warnings.length > 0 || mlResult.limitations.length > 0) && (
        <div className="border-t border-white/5 pt-3">
          {mlResult.warnings.map((w) => (
            <p key={w} className="text-xs text-amber-300">
              ⚠ {w}
            </p>
          ))}
          {mlResult.limitations.map((l) => (
            <p key={l} className="text-xs text-slate-500">
              · {l}
            </p>
          ))}
        </div>
      )}
      <Link
        to={`/datasets/${datasetId}/ml`}
        className="w-fit rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
      >
        Open ML tab
      </Link>
    </div>
  );
}
