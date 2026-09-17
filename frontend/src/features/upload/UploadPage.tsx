import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listDatasets, uploadDataset } from "../../api-client";
import { Card } from "../../components/Card";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { useAsync, useLazyAsync } from "../../hooks/useAsync";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function UploadDropzone({ onFileChosen }: { onFileChosen: (file: File) => void }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload a CSV dataset"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) onFileChosen(file);
      }}
      className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed p-10 text-center transition ${
        isDragOver ? "border-accent bg-accent/5" : "border-white/15 hover:border-white/30"
      }`}
    >
      <p className="text-sm font-medium text-slate-200">Drop a CSV file here, or click to browse</p>
      <p className="text-xs text-slate-500">Only .csv files are supported in this phase.</p>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFileChosen(file);
          e.target.value = "";
        }}
      />
    </div>
  );
}

function ExistingDatasets() {
  const navigate = useNavigate();
  const state = useAsync(listDatasets, []);

  if (state.status === "loading" || state.status === "idle") {
    return (
      <Card title="Your datasets">
        <LoadingSkeleton rows={3} />
      </Card>
    );
  }
  if (state.status === "error") {
    return (
      <Card title="Your datasets">
        <ErrorState message={state.message} onRetry={state.refetch} />
      </Card>
    );
  }
  if (state.data.length === 0) {
    return null;
  }

  return (
    <Card title="Your datasets" description="Previously uploaded, still available on this machine.">
      <ul className="flex flex-col divide-y divide-white/5">
        {state.data.map((dataset) => (
          <li key={dataset.id}>
            <button
              type="button"
              onClick={() => navigate(`/datasets/${dataset.id}`)}
              className="flex w-full items-center justify-between gap-4 py-3 text-left transition hover:text-accent"
            >
              <span className="truncate text-sm text-slate-200">{dataset.original_filename}</span>
              <span className="shrink-0 font-mono text-xs text-slate-500">
                {dataset.row_count}×{dataset.column_count} · {formatBytes(dataset.size_bytes)}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function UploadPage() {
  const navigate = useNavigate();
  const upload = useLazyAsync(uploadDataset);
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setValidationError(null);
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setValidationError(`Unsupported file type. Only .csv is supported in this phase.`);
      return;
    }
    const metadata = await upload.run(file);
    if (metadata) {
      navigate(`/datasets/${metadata.id}`);
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16">
      <header className="flex flex-col gap-2">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">AI Data Intelligence Workspace</p>
        <h1 className="text-3xl font-semibold text-slate-100">Upload a dataset</h1>
        <p className="text-sm text-slate-400">
          Upload a CSV file to see its ingestion status, quality profile, statistics, baseline ML results, and
          grounded AI analytics.
        </p>
      </header>

      <UploadDropzone onFileChosen={handleFile} />

      {validationError && <ErrorState message={validationError} />}
      {upload.status === "loading" && (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-accent" aria-hidden />
          Uploading and parsing your file…
        </div>
      )}
      {upload.status === "error" && <ErrorState message={upload.message} onRetry={upload.reset} />}

      <ExistingDatasets />
    </div>
  );
}
