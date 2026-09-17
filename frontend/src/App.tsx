import { Navigate, Route, Routes } from "react-router-dom";

import { AiPage } from "./features/ai/AiPage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { MlPage } from "./features/ml/MlPage";
import { QualityPage } from "./features/quality/QualityPage";
import { UploadPage } from "./features/upload/UploadPage";
import { OverviewPage } from "./features/workspace/OverviewPage";
import { WorkspaceLayout } from "./features/workspace/WorkspaceLayout";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/datasets/:datasetId" element={<WorkspaceLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="quality" element={<QualityPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="ml" element={<MlPage />} />
        <Route path="ai" element={<AiPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
