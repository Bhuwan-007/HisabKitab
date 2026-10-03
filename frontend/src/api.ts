import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  supplier: (id: number) => req<any>(`/suppliers/${id}`),
  suppliers: () => req<any[]>("/suppliers"),
  graph: () => req<any>("/graph"),
  rules: () => req<any>("/rules"),
  records: (source: string, status: string, page: number) => req<any>(`/reconciliation/records?source=${encodeURIComponent(source)}&status=${encodeURIComponent(status)}&page=${page}`),
  recordStatus: () => req<any>("/reconciliation/status"),
  runRecon: () => req<any>("/reconcile/run", { method: "POST" }),
  regenerate: () => req<any>("/data/seed", { method: "POST" }),
};

export function useSummary(period?: string) {
  return useQuery({
    queryKey: ["summary", period],
    queryFn: () => api.summary(period),
  });
}

export function useQueue() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["queue"],
    queryFn: () => api.queue(),
  });

  const updateItem = (updatedItem: QueueItem) => {
    queryClient.setQueryData(["queue"], (old: QueueItem[] | undefined) => {
      if (!old) return old;
      return old.map((x) => (x.id === updatedItem.id ? updatedItem : x));
    });
  };

  return { ...query, updateItem };
}

export function useSuppliers() {
  return useQuery({
    queryKey: ["suppliers"],
    queryFn: () => api.suppliers(),
  });
}

export function useGraph() {
  return useQuery({
    queryKey: ["graph"],
    queryFn: () => api.graph(),
  });
}

export function useRules() {
  return useQuery({
    queryKey: ["rules"],
    queryFn: () => api.rules(),
  });
}

export function useRecordStatus() {
  return useQuery({
    queryKey: ["recordStatus"],
    queryFn: () => api.recordStatus(),
  });
}
