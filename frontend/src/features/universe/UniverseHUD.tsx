import { useState } from "react";

import { useUniverseStore } from "../../state/universeStore";
import type { FeatureNode } from "../../universe/types";
import { Filters } from "./Filters";
import { Legend } from "./Legend";
import { Search } from "./Search";

/** The minimal spatial HUD (§33) — Search, Filters, Legend, Reset View, and the 2D/3D
 * toggle. Deliberately small: it never covers more than a thin strip of the viewport. */
export function UniverseHUD({ features, webglAvailable }: { features: FeatureNode[]; webglAvailable: boolean }) {
  const [legendOpen, setLegendOpen] = useState(false);
  const viewMode = useUniverseStore((s) => s.viewMode);
  const setViewMode = useUniverseStore((s) => s.setViewMode);
  const resetView = useUniverseStore((s) => s.resetView);

  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex flex-col gap-2 p-3">
      <div className="pointer-events-auto flex flex-wrap items-center justify-between gap-3 rounded-lg border border-white/10 bg-surface-raised/80 p-2 backdrop-blur">
        <div className="flex flex-wrap items-center gap-2">
          <Search features={features} />
          <Filters />
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              type="button"
              onClick={() => setLegendOpen((v) => !v)}
              aria-expanded={legendOpen}
              className="rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
            >
              Legend
            </button>
            {legendOpen && (
              // left-0, not right-0: the HUD can wrap this button near the left edge of a
              // narrow viewport (many filter chips + search sharing one row), and a
              // right-anchored popover would then render mostly off-screen/clipped by the
              // scene's own overflow-hidden container.
              <div className="absolute left-0 top-full z-20 mt-2">
                <Legend />
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={resetView}
            className="rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
          >
            Reset View
          </button>
          {webglAvailable && (
            <button
              type="button"
              onClick={() => setViewMode(viewMode === "3d" ? "2d" : "3d")}
              className="rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent"
            >
              {viewMode === "3d" ? "Switch to 2D" : "Switch to 3D"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
