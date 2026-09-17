/** A single correlation pair's coefficient as a horizontal magnitude bar, colored by
 * sign — never a heatmap gradient implying more precision than a single Pearson number
 * carries. Desaturated colors, consistent with 02_DOCS/UI_UX_SPEC.md §2's semantic-color
 * rule. */
export function CorrelationBar({ coefficient }: { coefficient: number }) {
  const magnitude = Math.min(Math.abs(coefficient), 1);
  const isPositive = coefficient >= 0;

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${isPositive ? "bg-sky-400/70" : "bg-rose-400/70"}`}
          style={{ width: `${magnitude * 100}%` }}
        />
      </div>
      <span className="w-14 text-right font-mono text-xs text-slate-300">{coefficient.toFixed(3)}</span>
    </div>
  );
}
