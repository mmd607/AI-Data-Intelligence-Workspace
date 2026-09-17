import type { ValueFrequency } from "../api-client";

/** A horizontal bar list for categorical top-values — same "render backend values
 * verbatim" rule as `Histogram`. */
export function FrequencyList({ values }: { values: ValueFrequency[] }) {
  if (values.length === 0) return null;
  const max = Math.max(...values.map((v) => v.percentage), 1);

  return (
    <ul className="flex flex-col gap-2">
      {values.map((v) => (
        <li key={v.value} className="flex items-center gap-2">
          <span className="w-24 truncate text-xs text-slate-400" title={v.value}>
            {v.value}
          </span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
            <div className="h-full rounded-full bg-accent/60" style={{ width: `${(v.percentage / max) * 100}%` }} />
          </div>
          <span className="w-16 text-right font-mono text-xs text-slate-300">
            {v.percentage}% ({v.count})
          </span>
        </li>
      ))}
    </ul>
  );
}
