/** Loading/error/empty state primitives — every data-bearing view uses one of these
 * three, per 02_DOCS/UI_UX_SPEC.md §8 ("Every data-bearing view must define: an empty
 * state ... a loading state (skeleton, not a spinner-only block) ... an error state"). */

export function LoadingSkeleton({ rows = 3, label = "Loading…" }: { rows?: number; label?: string }) {
  return (
    <div role="status" aria-label={label} className="flex flex-col gap-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 animate-pulse rounded bg-white/5" style={{ width: `${85 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-200">
      <p>{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-md border border-rose-400/30 px-3 py-1 text-xs font-medium text-rose-200 transition hover:bg-rose-500/10"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-dashed border-white/10 p-8 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
