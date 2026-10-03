import { useCallback, useEffect, useState } from "react";
import type { EvalMetrics, Health, QueueItem, Summary } from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new Error("Cannot reach the backend. Is it running on " + BASE + " ?");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = j?.error?.message || j?.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return res.json() as Promise<T>;
}

function unwrap<T>(r: any): T[] {
  if (Array.isArray(r)) return r as T[];
  return (r?.items ?? r?.results ?? r?.data ?? r?.rows ?? []) as T[];
}

export const api = {
  health: () => req<Health>("/health"),
  summary: (period?: string) => req<Summary>("/summary" + (period ? `?period=${encodeURIComponent(period)}` : "")),
  queue: async (): Promise<QueueItem[]> => {
    try {
      return unwrap<QueueItem>(await req<any>("/queue?page_size=200"));
    } catch {
      return unwrap<QueueItem>(await req<any>("/queue"));
    }
  },
  queueItem: (id: number | string) => req<QueueItem>(`/queue/${id}`),
  setStatus: (id: number, status: string) =>
    req<any>(`/queue/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
  explain: (id: number) => req<any>(`/queue/${id}/explain`, { method: "POST" }),
  draft: (id: number) => req<any>(`/queue/${id}/draft`, { method: "POST" }),
  audit: async (): Promise<any[]> => unwrap<any>(await req<any>("/audit?limit=100")),
  verify: () => req<{ valid: boolean; broken_at_id?: number | null }>("/audit/verify"),
  evaluation: async (): Promise<EvalMetrics> => {
    const r = await req<any>("/evaluation");
    return (r?.metrics ?? r) as EvalMetrics;
  },
};

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fn()
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e instanceof Error ? e : new Error(String(e))))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, setData, error, loading, reload };
}
