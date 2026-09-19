import { Link, Outlet, useLocation, useParams } from "react-router-dom";

import { getDataset } from "../../api-client";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { Tabs } from "../../components/Tabs";
import { useAsync } from "../../hooks/useAsync";
import { DatasetSessionProvider } from "../../state/DatasetSessionContext";

export function WorkspaceLayout() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const state = useAsync(() => getDataset(datasetId as string), [datasetId]);

  // The Universe is a spatial/canvas workspace, not a reading column — it earns far more
  // width on a large desktop display than the text/table-heavy 2D pages, which stay at a
  // comfortable, capped reading width (an editorial-width column is a deliberate
  // readability choice there, not something desktop size should stretch away). No content
  // max-width at all for the Universe — a hard pixel cap (tried during this pass: 1800px)
  // still left the flagship visualization looking small and margin-heavy at 2560px/4K, so
  // it instead scales continuously with the viewport, bounded only by padding. Both were
  // a fixed `max-w-5xl` (1024px, unchanged regardless of monitor size) before the Phase 08
  // desktop pass.
  const isUniverseRoute = useLocation().pathname.endsWith("/universe");
  const containerWidthClass = isUniverseRoute
    ? "max-w-none px-6 md:px-10 2xl:px-16"
    : "max-w-6xl px-6 2xl:max-w-[1400px] 2xl:px-10";

  return (
    <div className={`mx-auto flex min-h-screen ${containerWidthClass} flex-col gap-6 py-10`}>
      <header className="flex flex-col gap-3">
        <Link to="/" className="w-fit text-xs uppercase tracking-[0.2em] text-slate-500 hover:text-slate-300">
          ← AI Data Intelligence Workspace
        </Link>
        {state.status === "success" && (
          <h1 className="truncate text-2xl font-semibold text-slate-100">{state.data.original_filename}</h1>
        )}
        {state.status === "loading" && <LoadingSkeleton rows={1} />}
        <Tabs
          items={[
            { to: `/datasets/${datasetId}/universe`, label: "Universe" },
            { to: `/datasets/${datasetId}`, label: "Overview", end: true },
            { to: `/datasets/${datasetId}/quality`, label: "Quality" },
            { to: `/datasets/${datasetId}/analytics`, label: "Analytics" },
            { to: `/datasets/${datasetId}/ml`, label: "ML" },
            { to: `/datasets/${datasetId}/ai`, label: "AI Insights" },
          ]}
        />
      </header>

      {state.status === "loading" && <LoadingSkeleton rows={4} />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={state.refetch} />}
      {state.status === "success" && (
        <DatasetSessionProvider>
          <Outlet context={{ dataset: state.data }} />
        </DatasetSessionProvider>
      )}
    </div>
  );
}
