/** A computed numeric/data value — monospace treatment per 02_DOCS/UI_UX_SPEC.md §2
 * ("a monospace face for all numeric/data values ... gives computed numbers a distinct
 * visual identity from prose, reinforcing the computed-vs-AI-explanation separation"). */
export function StatValue({
  label,
  value,
  unit,
}: {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
}) {
  const display = value === null || value === undefined ? "—" : value;
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="text-xs uppercase tracking-wide text-slate-500">{label}</span>
      <span className="break-words font-mono text-lg text-slate-100">
        {display}
        {unit && display !== "—" ? <span className="ml-1 text-sm text-slate-500">{unit}</span> : null}
      </span>
    </div>
  );
}
