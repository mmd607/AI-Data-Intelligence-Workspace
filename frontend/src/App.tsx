import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { LoadingSkeleton } from "./components/StatusStates";
import { AiPage } from "./features/ai/AiPage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { MlPage } from "./features/ml/MlPage";
import { QualityPage } from "./features/quality/QualityPage";
import { UploadPage } from "./features/upload/UploadPage";
import { OverviewPage } from "./features/workspace/OverviewPage";
import { WorkspaceLayout } from "./features/workspace/WorkspaceLayout";

// Code-split: three.js/@react-three/fiber/drei are a genuinely large dependency
// (`npm run build`'s own chunk-size warning confirms it) that only the Universe tab
// needs — every other tab (and the upload landing page) should never pay that download
// cost. This is the concrete "performance" trade-off documented for this phase.
const UniversePage = lazy(() => import("./features/universe/UniversePage").then((m) => ({ default: m.UniversePage })));

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/datasets/:datasetId" element={<WorkspaceLayout />}>
        <Route index element={<OverviewPage />} />
        <Route
          path="universe"
          element={
            <Suspense fallback={<LoadingSkeleton rows={6} label="Loading the Universe…" />}>
              <UniversePage />
            </Suspense>
          }
        />
        <Route path="quality" element={<QualityPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="ml" element={<MlPage />} />
        <Route path="ai" element={<AiPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
