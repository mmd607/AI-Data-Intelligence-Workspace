import { motion } from "framer-motion";
import { useEffect, useState } from "react";

import { ApiError, getHealth } from "./api-client/client";
import type { HealthResponse } from "./api-client/types";
import { UniversePlaceholder } from "./scene/UniversePlaceholder";

type ConnectionState =
  | { kind: "loading" }
  | { kind: "connected"; health: HealthResponse }
  | { kind: "error"; message: string };

function useBackendHealth(): ConnectionState {
  const [state, setState] = useState<ConnectionState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    getHealth()
      .then((health) => {
        if (!cancelled) setState({ kind: "connected", health });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message = error instanceof ApiError ? error.message : "Unable to reach the backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

function ConnectivityBadge({ state }: { state: ConnectionState }) {
  if (state.kind === "loading") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-surface-raised px-3 py-1 text-sm text-slate-400">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-500" aria-hidden />
        Checking backend…
      </span>
    );
  }

  if (state.kind === "connected") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-surface-raised px-3 py-1 text-sm text-emerald-300">
        <span className="h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
        Backend connected — {state.health.environment}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-sm text-amber-300">
      <span className="h-2 w-2 rounded-full bg-amber-400" aria-hidden />
      Backend unavailable — {state.message}
    </span>
  );
}

export default function App() {
  const health = useBackendHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-16">
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-3"
      >
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
          AI Data Intelligence Workspace
        </p>
        <h1 className="text-3xl font-semibold text-slate-100">Data Intelligence Universe</h1>
        <p className="max-w-prose text-sm text-slate-400">
          Phase 01 foundation shell. This proves the frontend/backend/3D-render toolchain
          works end-to-end — the real Universe interface is built in Phase 07.
        </p>
        <ConnectivityBadge state={health} />
      </motion.header>

      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.15 }}
        className="flex flex-col gap-3"
      >
        <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
          Render pipeline check
        </h2>
        <UniversePlaceholder />
      </motion.section>
    </main>
  );
}
