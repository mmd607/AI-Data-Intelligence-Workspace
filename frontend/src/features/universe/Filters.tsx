import { hasActiveFilters } from "../../universe/filtering";
import { useUniverseStore, type UniverseFilters } from "../../state/universeStore";

const FILTER_LABELS: Record<keyof UniverseFilters, string> = {
  numeric: "Numeric",
  categorical: "Categorical",
  missing: "Has missing data",
  qualityWarning: "Quality warning",
  correlated: "Correlated",
  mlRelated: "ML-related",
};

/** Feature filters (§24) — only the categories real data actually supports; each maps
 * directly to a real field (`universe/filtering.ts`), nothing invented. */
export function Filters() {
  const filters = useUniverseStore((s) => s.filters);
  const toggleFilter = useUniverseStore((s) => s.toggleFilter);
  const clearFilters = useUniverseStore((s) => s.clearFilters);

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {(Object.keys(FILTER_LABELS) as (keyof UniverseFilters)[]).map((key) => (
        <button
          key={key}
          type="button"
          onClick={() => toggleFilter(key)}
          aria-pressed={filters[key]}
          className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition ${
            filters[key]
              ? "border-accent/50 bg-accent/10 text-accent"
              : "border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200"
          }`}
        >
          {FILTER_LABELS[key]}
        </button>
      ))}
      {hasActiveFilters(filters) && (
        <button type="button" onClick={clearFilters} className="text-[11px] text-slate-500 underline hover:text-slate-300">
          Clear
        </button>
      )}
    </div>
  );
}
