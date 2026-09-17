import { useOutletContext } from "react-router-dom";

import type { DatasetMetadata } from "../../api-client";

interface WorkspaceOutletContext {
  dataset: DatasetMetadata;
}

/** Typed access to the dataset `WorkspaceLayout` already fetched — nested routes never
 * re-fetch dataset metadata themselves. */
export function useWorkspaceDataset(): DatasetMetadata {
  return useOutletContext<WorkspaceOutletContext>().dataset;
}
