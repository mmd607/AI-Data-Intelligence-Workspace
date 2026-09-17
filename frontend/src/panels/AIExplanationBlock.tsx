import type { AIExplanation } from "../api-client";

/**
 * Renders an AI-generated explanation as a visually distinct block, per
 * 02_DOCS/UI_UX_SPEC.md §4.6: "a subtler background tint, a small mode-attribution label
 * ... positioned below/subordinate to the computed data it explains ... AI-generated
 * text uses standard sans-serif prose. The two must never share a visual style."
 *
 * AI output is untrusted content (01_PHASES/PHASE_06.../PHASE_PROMPT.md §23) — rendered
 * as plain text only, never `dangerouslySetInnerHTML`, so nothing it returns can inject
 * markup or execute.
 */
export function AIExplanationBlock({
  explanation,
  limitations,
}: {
  explanation: AIExplanation | null;
  limitations?: string[];
}) {
  if (!explanation) return null;

  return (
    <div className="mt-4 rounded-lg border border-accent/20 bg-accent/5 p-4">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-accent/80">
        AI explanation — {explanation.provider}
        {explanation.model ? ` (${explanation.model})` : ""}
      </p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-200">{explanation.text}</p>
      {limitations && limitations.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1 border-t border-white/5 pt-2 text-xs text-slate-500">
          {limitations.map((limitation) => (
            <li key={limitation}>· {limitation}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AIUnavailableNotice({ reason }: { reason: string | null }) {
  return (
    <div className="mt-4 rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-slate-400">
      AI analytics is currently unavailable{reason ? ` (${reason})` : ""}. Deterministic analytics remain
      available.
    </div>
  );
}
