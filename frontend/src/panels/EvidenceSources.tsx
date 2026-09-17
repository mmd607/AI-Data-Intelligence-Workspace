const SOURCE_LABELS: Record<string, string> = {
  dataset_metadata: "Dataset Profile",
  quality_report: "Data Quality Report",
  correlation_report: "Correlation Analysis",
  column_statistics: "Column Statistics",
  ml_result: "ML Result",
};

/** Renders the real `evidence_sources` the backend returned — never a fabricated
 * citation (01_PHASES/PHASE_06.../PHASE_PROMPT.md §13: "Do not invent evidence
 * references."). */
export function EvidenceSources({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
      <span>Supported by:</span>
      {sources.map((source) => (
        <span key={source} className="rounded-full border border-white/10 px-2 py-0.5">
          {SOURCE_LABELS[source] ?? source}
        </span>
      ))}
    </div>
  );
}
