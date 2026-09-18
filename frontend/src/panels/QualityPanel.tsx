import type { QualitySummary } from "../api-client";
import { Badge } from "../components/Badge";
import { severityToTone } from "../components/severity";
import { EmptyState } from "../components/StatusStates";

/** Quality domain detail — presentational only; `quality` is the same `QualitySummary`
 * `UniversePage` already fetched for the graph (no duplicated fetch, per this phase's
 * module-boundary rule). */
export function QualityPanel({ quality }: { quality: QualitySummary | null }) {
  if (!quality) return <EmptyState title="Not loaded yet" hint="Quality data is still loading." />;
  if (quality.findings.length === 0) {
    return <EmptyState title="No data-quality findings" hint="This dataset passed every deterministic quality check." />;
  }

  return (
    <ul className="flex flex-col divide-y divide-white/5">
      {quality.findings.map((finding, i) => (
        <li key={`${finding.code}-${i}`} className="flex flex-col gap-1 py-3">
          <div className="flex items-center gap-2">
            <Badge tone={severityToTone(finding.severity)}>{finding.severity}</Badge>
            <span className="font-mono text-xs text-slate-500">{finding.code}</span>
            {finding.column && <span className="font-mono text-xs text-slate-400">· {finding.column}</span>}
          </div>
          <p className="text-sm text-slate-300">{finding.message}</p>
        </li>
      ))}
    </ul>
  );
}
