import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../api-client";

export type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; message: string; status_code?: number; code?: string };

function describeError(error: unknown): { message: string; status_code?: number; code?: string } {
  if (error instanceof ApiError) {
    return { message: error.message, status_code: error.status, code: error.code };
  }
  return { message: "An unexpected error occurred." };
}

/**
 * Runs `fn` on mount (and whenever `deps` changes), tracking loading/success/error state.
 * Every data-bearing view uses this (or `useLazyAsync` below) instead of a bespoke
 * `useEffect` + `useState` pair, per 02_DOCS/UI_UX_SPEC.md §8's loading/error requirement.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: React.DependencyList): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });

    fnRef
      .current()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: "error", ...describeError(error) });
      });

    return () => {
      cancelled = true;
    };
  }, [...deps, tick]);

  const refetch = useCallback(() => setTick((n) => n + 1), []);
  return { ...state, refetch };
}

/**
 * Like `useAsync`, but does not run automatically — `run(...)` triggers the call. Used
 * for user-initiated actions (upload, train, ask a question) rather than view-mount data
 * loads.
 */
export function useLazyAsync<Args extends unknown[], T>(
  fn: (...args: Args) => Promise<T>,
): AsyncState<T> & { run: (...args: Args) => Promise<T | undefined>; reset: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const run = useCallback(async (...args: Args) => {
    setState({ status: "loading" });
    try {
      const data = await fnRef.current(...args);
      setState({ status: "success", data });
      return data;
    } catch (error) {
      setState({ status: "error", ...describeError(error) });
      return undefined;
    }
  }, []);

  const reset = useCallback(() => setState({ status: "idle" }), []);

  return { ...state, run, reset };
}
