import { Link } from "react-router-dom";

import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { EmptyState } from "../components/StatusStates";
import { useUniverseStore } from "../state/universeStore";
import { filterFeatureNodes, hasActiveFilters } from "./filtering";
import type { UniverseGraph } from "./types";

const DOMAIN_ROUTE: Record<string, string> = {
  profile: "",
  quality: "quality",
  analytics: "analytics",
  ml: "ml",
  ai: "ai",
};

/**
 * The 2D list/table fallback (`02_DOCS/UI_UX_SPEC.md` §3/§4.7) — the same graph the 3D
 * scene renders, presented as plain, fully accessible markup. Used when WebGL/performance
 * detection rules out the 3D scene, on narrow (mobile) viewports by default, and whenever
 * `UniverseErrorBoundary` catches a 3D render failure. Reaches full data parity with the
 * 3D view; only the spatial metaphor is lost.
 */
export function UniverseFallback({ graph, datasetId, reason }: { graph: UniverseGraph; datasetId: string; reason?: string }) {
  const searchQuery = useUniverseStore((s) => s.searchQuery);
  const setSearchQuery = useUniverseStore((s) => s.setSearchQuery);
  const filters = useUniverseStore((s) => s.filters);
  const selectedNodeId = useUniverseStore((s) => s.selectedNodeId);
  const selectNode = useUniverseStore((s) => s.selectNode);

  const visibleFeatures = filterFeatureNodes(graph.featureNodesByDomain.profile, filters, searchQuery, {
    correlatedColumns: new Set(graph.featureNodesByDomain.analytics.map((n) => n.column)),
    mlColumns: new Set(),
  });

  return (
    <div className="flex flex-col gap-6">
      {reason && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-200">{reason}</div>
      )}

      <Card title={graph.datasetNode.label} description="2D view — every value below is identical to the 3D Universe, presented as plain data.">
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Rows</p>
              <p className="font-mono text-lg text-slate-100">{graph.datasetNode.rowCount.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Columns</p>
              <p className="font-mono text-lg text-slate-100">{graph.datasetNode.columnCount}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => selectNode("dataset")}
            className="w-fit rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-accent hover:text-accent"
          >
            View dataset details
          </button>
        </div>
      </Card>

      <Card title="Domains" description="Each domain links to its full detail tab.">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {graph.domainNodes.map((domain) => (
            <Link
              key={domain.id}
              to={`/datasets/${datasetId}/${DOMAIN_ROUTE[domain.domain]}`}
              onClick={() => selectNode(domain.id)}
              className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] p-3 transition hover:border-accent/40"
            >
              <div>
                <p className="text-sm font-medium text-slate-200">{domain.label}</p>
                <p className="text-xs text-slate-500">{domain.summary}</p>
              </div>
              <Badge tone={domain.available ? "good" : "neutral"}>{domain.available ? "Available" : "Empty"}</Badge>
            </Link>
          ))}
        </div>
      </Card>

      <Card title="Features" description="Search or filter the dataset's columns.">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search columns…"
          aria-label="Search columns"
          className="mb-4 w-full rounded-md border border-white/10 bg-surface px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600"
        />
        {visibleFeatures.length === 0 && (
          <EmptyState
            title={hasActiveFilters(filters) || searchQuery ? "No columns match" : "No columns profiled yet"}
            hint={hasActiveFilters(filters) || searchQuery ? "Try clearing the search or filters." : undefined}
          />
        )}
        {visibleFeatures.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Column</th>
                  <th className="py-2 pr-4 font-medium">Type</th>
                  <th className="py-2 pr-4 text-right font-medium">Missing</th>
                  <th className="py-2 font-medium">Quality</th>
                </tr>
              </thead>
              <tbody>
                {visibleFeatures.map((feature) => (
                  <tr
                    key={feature.id}
                    onClick={() => selectNode(feature.id)}
                    className={`cursor-pointer border-b border-white/5 last:border-0 hover:bg-white/5 ${
                      selectedNodeId === feature.id ? "bg-accent/5" : ""
                    }`}
                  >
                    <td className="py-2 pr-4 font-mono text-slate-200">{feature.column}</td>
                    <td className="py-2 pr-4 text-slate-400">{feature.semanticType}</td>
                    <td className="py-2 pr-4 text-right font-mono text-xs text-slate-300">{feature.nullPercentage}%</td>
                    <td className="py-2">
                      {feature.hasQualityCritical && <Badge tone="critical">critical</Badge>}
                      {!feature.hasQualityCritical && feature.hasQualityWarning && <Badge tone="warning">warning</Badge>}
                      {!feature.hasQualityCritical && !feature.hasQualityWarning && <Badge tone="good">clean</Badge>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {graph.correlationEdges.length > 0 && (
        <Card title="Strongest correlations" description="The same pairs the 3D Analytics ring would render as edges.">
          <ul className="flex flex-col divide-y divide-white/5">
            {graph.correlationEdges.map((edge) => (
              <li key={edge.id} className="flex items-center justify-between py-2">
                <span className="font-mono text-xs text-slate-400">
                  {edge.source.replace("feature:analytics:", "")} × {edge.target.replace("feature:analytics:", "")}
                </span>
                <span className="font-mono text-sm text-slate-200">{edge.coefficient.toFixed(3)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
