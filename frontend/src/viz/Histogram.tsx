import type { HistogramBin } from "../api-client";

/**
 * A minimal SVG bar histogram rendering the backend's own bins verbatim — no client-side
 * binning/recalculation (01_PHASES/PHASE_06.../PHASE_PROMPT.md §9: "The backend remains
 * the source of truth"). Deliberately hand-rolled rather than a charting dependency: this
 * phase prioritizes functional correctness over final visual polish (Phase 07 owns the
 * visual identity), and a fixed bar chart doesn't need a general-purpose library.
 */
export function Histogram({ bins, height = 120 }: { bins: HistogramBin[]; height?: number }) {
  if (bins.length === 0) return null;

  const maxCount = Math.max(...bins.map((b) => b.count), 1);
  const width = 320;
  const barGap = 2;
  const barWidth = width / bins.length - barGap;

  return (
    <svg viewBox={`0 0 ${width} ${height + 16}`} width="100%" height={height + 16} role="img" aria-label="Histogram">
      {bins.map((bin, i) => {
        const barHeight = (bin.count / maxCount) * height;
        const x = i * (barWidth + barGap);
        return (
          <g key={`${bin.bin_start}-${bin.bin_end}`}>
            <rect
              x={x}
              y={height - barHeight}
              width={Math.max(barWidth, 1)}
              height={Math.max(barHeight, 1)}
              className="fill-accent/60"
            >
              <title>
                {bin.bin_start.toFixed(2)}–{bin.bin_end.toFixed(2)}: {bin.count}
              </title>
            </rect>
          </g>
        );
      })}
      <line x1={0} y1={height} x2={width} y2={height} className="stroke-white/10" strokeWidth={1} />
    </svg>
  );
}
