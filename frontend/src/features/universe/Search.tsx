import { useMemo, useState } from "react";

import { useUniverseStore } from "../../state/universeStore";
import type { FeatureNode } from "../../universe/types";

/** Dataset feature search (§23) — narrows the same feature ring the scene/fallback both
 * render, and selecting a result focuses the camera on the real matching node. */
export function Search({ features }: { features: FeatureNode[] }) {
  const searchQuery = useUniverseStore((s) => s.searchQuery);
  const setSearchQuery = useUniverseStore((s) => s.setSearchQuery);
  const focusNode = useUniverseStore((s) => s.focusNode);
  const [open, setOpen] = useState(false);

  const matches = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return [];
    return features.filter((f) => f.column.toLowerCase().includes(query)).slice(0, 8);
  }, [features, searchQuery]);

  return (
    <div className="relative">
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => {
          setSearchQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        placeholder="Search columns…"
        aria-label="Search columns"
        className="w-48 rounded-md border border-white/10 bg-surface px-3 py-1.5 text-xs text-slate-100 placeholder:text-slate-600"
      />
      {open && matches.length > 0 && (
        <ul className="absolute left-0 top-full z-10 mt-1 w-56 rounded-md border border-white/10 bg-surface-raised p-1 shadow-lg">
          {matches.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  focusNode(m.id);
                  setOpen(false);
                }}
                className="w-full rounded px-2 py-1 text-left font-mono text-xs text-slate-300 hover:bg-white/5 hover:text-accent"
              >
                {m.column} <span className="text-slate-600">· {m.semanticType}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
