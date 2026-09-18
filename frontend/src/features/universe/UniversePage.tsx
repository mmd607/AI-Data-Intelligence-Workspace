import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { getAiStatus, getCorrelation, getDatasetProfile, getQualitySummary } from "../../api-client";
import { useAsync } from "../../hooks/useAsync";
import { AIInsightPanel } from "../../panels/AIInsightPanel";
import { CorrelationPanel } from "../../panels/CorrelationPanel";
import { DatasetPanel } from "../../panels/DatasetPanel";
import { DetailPanel } from "../../panels/DetailPanel";
import { FeaturePanel } from "../../panels/FeaturePanel";
import { MLPanel } from "../../panels/MLPanel";
import { QualityPanel } from "../../panels/QualityPanel";
import { useUniverseStore } from "../../state/universeStore";
import { useDatasetSession } from "../../state/useDatasetSession";
import { buildUniverseGraph } from "../../universe/mapping";
import { detectPerformanceTier, usePrefersReducedMotion } from "../../universe/tiers";
import { UniverseErrorBoundary } from "../../universe/UniverseErrorBoundary";
import { UniverseFallback } from "../../universe/UniverseFallback";
import { UniverseScene } from "../../universe/UniverseScene";
import { useWorkspaceDataset } from "../workspace/useWorkspaceDataset";
import { UniverseHUD } from "./UniverseHUD";

export function UniversePage() {
  const dataset = useWorkspaceDataset();
  const { lastMlResult } = useDatasetSession();
  const profile = useAsync(() => getDatasetProfile(dataset.id), [dataset.id]);
  const quality = useAsync(() => getQualitySummary(dataset.id), [dataset.id]);
  const correlation = useAsync(() => getCorrelation(dataset.id), [dataset.id]);
  const aiStatus = useAsync(getAiStatus, []);

  const profileData = profile.status === "success" ? profile.data : null;
  const qualityData = quality.status === "success" ? quality.data : null;
  const correlationData = correlation.status === "success" ? correlation.data : null;
  const aiStatusData = aiStatus.status === "success" ? aiStatus.data : null;

  const reducedMotion = usePrefersReducedMotion();
  const [tier, setTier] = useState(() => detectPerformanceTier());
  useEffect(() => {
    function handleResize() {
      setTier(detectPerformanceTier());
    }
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const viewMode = useUniverseStore((s) => s.viewMode);
  const setViewMode = useUniverseStore((s) => s.setViewMode);
  const selectedNodeId = useUniverseStore((s) => s.selectedNodeId);
  const selectNode = useUniverseStore((s) => s.selectNode);

  // Mobile/no-WebGL defaults to the 2D view (UI_UX_SPEC.md §6) — a one-time default on
  // load, never re-forced on a later resize, so an explicit 2D/3D toggle isn't stomped.
  // `effectiveViewMode` (not the raw store value) drives whether Canvas mounts, computed
  // synchronously during render: waiting for an effect to correct `viewMode` after the
  // fact would let Canvas mount for one commit first, which is exactly the crash this
  // page's own error boundary exists to catch — better to never attempt it at all.
  const defaultViewModeApplied = useRef(false);
  const effectiveViewMode = defaultViewModeApplied.current ? viewMode : tier.forceFallback ? "2d" : viewMode;
  useEffect(() => {
    if (defaultViewModeApplied.current) return;
    defaultViewModeApplied.current = true;
    if (tier.forceFallback && viewMode !== "2d") setViewMode("2d");
  }, [tier.forceFallback, viewMode, setViewMode]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") selectNode(null);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectNode]);

  const graph = useMemo(
    () =>
      buildUniverseGraph({
        dataset,
        profile: profileData,
        quality: qualityData,
        correlation: correlationData,
        mlResult: lastMlResult,
        aiStatus: aiStatusData,
      }),
    [dataset, profileData, qualityData, correlationData, lastMlResult, aiStatusData],
  );

  const showCanvas = effectiveViewMode === "3d" && tier.webglAvailable;

  const panel = useMemo(() => {
    if (!selectedNodeId) return null;
    if (selectedNodeId === "dataset") {
      return {
        title: dataset.original_filename,
        subtitle: "Dataset overview",
        content: (
          <DatasetPanel
            dataset={dataset}
            profile={profileData}
            quality={qualityData}
            correlation={correlationData}
            mlResult={lastMlResult}
            aiStatus={aiStatusData}
          />
        ),
      };
    }
    if (selectedNodeId === "domain:profile") {
      return {
        title: "Data Profile",
        subtitle: profileData ? `${profileData.column_count} columns profiled` : undefined,
        content: (
          <div className="flex flex-col gap-3 text-sm text-slate-400">
            <p>Select a feature node (or search above) to see a column's full profile.</p>
            <Link to={`/datasets/${dataset.id}`} className="w-fit rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:border-accent hover:text-accent">
              Open Overview tab
            </Link>
          </div>
        ),
      };
    }
    if (selectedNodeId === "domain:quality") {
      return { title: "Data Quality", content: <QualityPanel quality={qualityData} /> };
    }
    if (selectedNodeId === "domain:analytics") {
      return { title: "Analytics", content: <CorrelationPanel correlation={correlationData} /> };
    }
    if (selectedNodeId === "domain:ml") {
      return { title: "ML", content: <MLPanel datasetId={dataset.id} mlResult={lastMlResult} /> };
    }
    if (selectedNodeId === "domain:ai") {
      return { title: "AI Insights", content: <AIInsightPanel datasetId={dataset.id} aiStatus={aiStatusData} /> };
    }
    if (selectedNodeId.startsWith("feature:")) {
      const column = selectedNodeId.split(":").slice(2).join(":");
      const columnProfile = profileData?.columns.find((c) => c.name === column);
      const featureNode =
        graph.featureNodesByDomain.profile.find((f) => f.column === column) ??
        graph.featureNodesByDomain.analytics.find((f) => f.column === column);
      if (!columnProfile || !featureNode) return null;
      return {
        title: column,
        subtitle: "Feature detail",
        content: (
          <FeaturePanel
            datasetId={dataset.id}
            column={columnProfile}
            hasQualityWarning={featureNode.hasQualityWarning}
            hasQualityCritical={featureNode.hasQualityCritical}
          />
        ),
      };
    }
    return null;
  }, [selectedNodeId, dataset, profileData, qualityData, correlationData, lastMlResult, aiStatusData, graph]);

  const fallbackReason = !tier.webglAvailable
    ? "WebGL is not available on this device — showing the 2D view. All data remains fully accessible."
    : undefined;

  return (
    <div className="relative flex h-[calc(100vh-260px)] min-h-[540px] gap-0 overflow-hidden rounded-xl border border-white/10 bg-surface-raised">
      <div className="relative min-w-0 flex-1">
        {showCanvas ? (
          <UniverseErrorBoundary
            fallback={
              <div className="h-full overflow-y-auto p-4">
                <UniverseFallback graph={graph} datasetId={dataset.id} reason="3D visualization is unavailable — showing the 2D view. All data remains fully accessible." />
              </div>
            }
          >
            <UniverseScene graph={graph} tier={tier.tier} reducedMotion={reducedMotion} />
            <UniverseHUD features={graph.featureNodesByDomain.profile} webglAvailable={tier.webglAvailable} />
          </UniverseErrorBoundary>
        ) : (
          <div className="h-full overflow-y-auto p-4">
            {tier.webglAvailable && (
              <button
                type="button"
                onClick={() => setViewMode("3d")}
                className="mb-4 rounded-md border border-accent/30 px-3 py-1.5 text-xs font-medium text-accent hover:bg-accent/10"
              >
                Try 3D Universe
              </button>
            )}
            <UniverseFallback graph={graph} datasetId={dataset.id} reason={fallbackReason} />
          </div>
        )}
      </div>

      {panel && (
        <DetailPanel open={selectedNodeId !== null} onClose={() => selectNode(null)} title={panel.title} subtitle={panel.subtitle}>
          {panel.content}
        </DetailPanel>
      )}
    </div>
  );
}
