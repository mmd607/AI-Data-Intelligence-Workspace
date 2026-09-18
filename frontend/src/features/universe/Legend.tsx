/** A concise legend documenting every visual encoding used in the scene (§25/§26) — the
 * user should never have to guess what a color, size, or line means. */
export function Legend() {
  return (
    <div className="flex w-64 flex-col gap-3 rounded-lg border border-white/10 bg-surface-raised/95 p-4 text-xs text-slate-300 shadow-lg backdrop-blur">
      <div>
        <p className="mb-1 font-medium text-slate-200">Node types</p>
        <ul className="flex flex-col gap-1">
          <li className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" /> Dataset core
          </li>
          <li className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-accent" /> Domain (Profile / Quality / Analytics / ML)
          </li>
          <li className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm bg-accent-secondary" /> AI Insights domain
          </li>
          <li className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent" /> Numeric feature
          </li>
          <li className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent-secondary" /> Categorical feature
          </li>
        </ul>
      </div>
      <div>
        <p className="mb-1 font-medium text-slate-200">Encodings</p>
        <ul className="flex flex-col gap-1">
          <li>Feature size → missing-value percentage (bigger = more missing)</li>
          <li>Edge thickness → strength of correlation (|coefficient|)</li>
          <li>
            Edge color → <span className="text-sky-400">positive</span> /{" "}
            <span className="text-rose-400">negative</span> correlation — never causation
          </li>
        </ul>
      </div>
      <div>
        <p className="mb-1 font-medium text-slate-200">States</p>
        <ul className="flex flex-col gap-1">
          <li>Bright / enlarged → hovered or selected</li>
          <li>
            <span className="text-rose-400">Red tint</span> → critical quality finding
          </li>
          <li>Dim / low-opacity → no data yet</li>
        </ul>
      </div>
    </div>
  );
}
