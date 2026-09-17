import { useContext } from "react";

import { DatasetSessionContext } from "./sessionContextValue";

export function useDatasetSession() {
  const ctx = useContext(DatasetSessionContext);
  if (!ctx) throw new Error("useDatasetSession must be used within a DatasetSessionProvider");
  return ctx;
}
