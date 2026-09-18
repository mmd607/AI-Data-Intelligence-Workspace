import { Link, Outlet, useParams } from "react-router-dom";

import { getDataset } from "../../api-client";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { Tabs } from "../../components/Tabs";
import { useAsync } from "../../hooks/useAsync";
import { DatasetSessionProvider } from "../../state/DatasetSessionContext";

export function WorkspaceLayout() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const state = useAsync(() => getDataset(datasetId as string), [datasetId]);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-6 py-10">
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
