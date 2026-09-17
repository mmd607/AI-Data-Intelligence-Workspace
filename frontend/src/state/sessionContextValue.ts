import { createContext } from "react";

import type { ModelResult } from "../api-client";

export interface DatasetSessionValue {
  lastMlResult: ModelResult | null;
  setLastMlResult: (result: ModelResult | null) => void;
}

export const DatasetSessionContext = createContext<DatasetSessionValue | null>(null);
