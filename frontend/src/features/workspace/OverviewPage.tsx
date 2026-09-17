import { getDatasetProfile } from "../../api-client";
import type { ColumnProfile } from "../../api-client";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { ErrorState, LoadingSkeleton } from "../../components/StatusStates";
import { StatValue } from "../../components/StatValue";
import { useAsync } from "../../hooks/useAsync";
import { useWorkspaceDataset } from "./useWorkspaceDataset";

function ColumnRow({ column }: { column: ColumnProfile }) {
  const representative = column.sample_values.slice(0, 3).map((v) => (v === null ? "∅" : String(v)));
  return (
    <tr className="border-b border-white/5 last:border-0">
      <td className="py-2 pr-4 font-mono text-sm text-slate-200">{column.name}</td>
      <td className="py-2 pr-4">
        <Badge tone="neutral">{column.semantic_type}</Badge>
      </td>
      <td className="py-2 pr-4 font-mono text-xs text-slate-400">{column.pandas_dtype}</td>
      <td className="py-2 pr-4 text-right font-mono text-xs text-slate-300">
        {column.null_count} ({column.null_percentage}%)
      </td>
      <td className="py-2 pr-4 text-right font-mono text-xs text-slate-300">
        {column.unique_count} ({column.unique_percentage}%)
      </td>
      <td className="py-2 text-xs text-slate-500">{representative.join(", ") || "—"}</td>
    </tr>
  );
}

export function OverviewPage() {
  const dataset = useWorkspaceDataset();
  const profile = useAsync(() => getDatasetProfile(dataset.id), [dataset.id]);

  return (
    <div className="flex flex-col gap-6">
      <Card title="Overview">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatValue label="Rows" value={dataset.row_count} />
          <StatValue label="Columns" value={dataset.column_count} />
          <StatValue label="Size" value={(dataset.size_bytes / 1024).toFixed(1)} unit="KB" />
          <StatValue label="Duplicate rows" value={dataset.duplicate_row_count} />
        </div>
        {profile.status === "success" && (
          <div className="mt-4 grid grid-cols-2 gap-4 border-t border-white/5 pt-4 sm:grid-cols-4">
            <StatValue label="Memory (est.)" value={(profile.data.memory_usage_bytes / 1024).toFixed(1)} unit="KB" />
            <StatValue label="Missing cells" value={profile.data.missing.total_missing_cells} />
            <StatValue label="Missing %" value={profile.data.missing.missing_percentage} unit="%" />
            <StatValue label="Duplicate %" value={profile.data.duplicate_row_percentage} unit="%" />
          </div>
        )}
      </Card>

      <Card title="Columns" description="Structural profile of every column, computed by the backend.">
        {profile.status === "loading" && <LoadingSkeleton rows={5} />}
        {profile.status === "error" && <ErrorState message={profile.message} onRetry={profile.refetch} />}
        {profile.status === "success" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Name</th>
                  <th className="py-2 pr-4 font-medium">Type</th>
                  <th className="py-2 pr-4 font-medium">Raw dtype</th>
                  <th className="py-2 pr-4 text-right font-medium">Nulls</th>
                  <th className="py-2 pr-4 text-right font-medium">Unique</th>
                  <th className="py-2 font-medium">Sample values</th>
                </tr>
              </thead>
              <tbody>
                {profile.data.columns.map((column) => (
                  <ColumnRow key={column.name} column={column} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
