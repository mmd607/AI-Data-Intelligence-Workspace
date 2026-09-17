/** Semantic-state badge (§2: desaturated, low-luminance variants, never saturated neon). */
export type BadgeTone = "neutral" | "good" | "warning" | "critical" | "info";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "border-white/10 bg-white/5 text-slate-300",
  good: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  critical: "border-rose-500/30 bg-rose-500/10 text-rose-300",
  info: "border-sky-500/30 bg-sky-500/10 text-sky-300",
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
