"use client";

import { useEffect, useState } from "react";
import { ApiError } from "./api";

interface State<T> {
  key: string | null;
  data?: T;
  error?: string;
  fieldErrors?: Record<string, string>;
  lastData?: T;
}

/** Runs fetcher whenever key changes. A null key means there is nothing to fetch yet. */
export function useRequest<T>(key: string | null, fetcher: () => Promise<T>) {
  const [state, setState] = useState<State<T>>({ key: null });

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    fetcher()
      .then((data) => !cancelled && setState({ key, data, lastData: data }))
      .catch((err: unknown) => {
        if (cancelled) return;
        const fieldErrors = err instanceof ApiError ? err.fieldErrors : {};
        const message = Object.keys(fieldErrors).length
          ? Object.entries(fieldErrors).map(([f, m]) => `${f}: ${m}`).join("; ")
          : err instanceof Error ? err.message : String(err);
        setState((prev) => ({ key, error: message, fieldErrors, lastData: prev.lastData }));
      });
    return () => {
      cancelled = true;
    };
    // fetcher is recreated every render; key captures everything it depends on.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const current = state.key === key;
  return {
    data: current ? state.data : undefined,
    error: current ? state.error : undefined,
    fieldErrors: (current && state.fieldErrors) || {},
    loading: key !== null && !current,
    /** Most recent successful result, kept while a new request loads or after it fails. */
    lastData: state.lastData,
  };
}
