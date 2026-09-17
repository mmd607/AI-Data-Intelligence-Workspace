import { useMemo, useState, type ReactNode } from "react";

import type { ModelResult } from "../api-client";
import { DatasetSessionContext } from "./sessionContextValue";

/**
 * Per-dataset client-only session state — not server state, so it belongs here rather
 * than being re-fetched (02_DOCS's "avoid duplicated server state" guidance).
 *
 * The backend has no model-persistence layer (ADR-013): a trained `ModelResult` only
 * ever exists as the direct response of `POST .../ml/train`. The AI `ml_explanation`
 * capability requires the caller to supply that exact result back
 * (`backend/app/ai/evidence.py::build_ml_explanation_evidence`), so the last one trained
 * in this browser session is remembered here for the AI page to reuse — never
 * reconstructed or guessed.
 */
export function DatasetSessionProvider({ children }: { children: ReactNode }) {
  const [lastMlResult, setLastMlResult] = useState<ModelResult | null>(null);
  const value = useMemo(() => ({ lastMlResult, setLastMlResult }), [lastMlResult]);
  return <DatasetSessionContext.Provider value={value}>{children}</DatasetSessionContext.Provider>;
}
