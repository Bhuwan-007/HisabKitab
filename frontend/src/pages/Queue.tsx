import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, useQueue } from "../api";
import { ACTION_LABEL, BUCKET_LABEL, SEVERITY_LABEL, bucketTone, daysLeftLabel, formatDate, formatINR, titleCase } from "../format";
import { Badge, Empty, ErrorBox, Loading } from "../components/ui";
import Drawer, { invoiceLabel, supplierName } from "../components/Drawer";
import type { QueueItem } from "../types";

const BUCKET_OPTIONS: [string, string][] = [
  ["ACTION", "Needs attention"],
  ["AT_RISK", "At risk"],
  ["NEEDS_FIX", "Needs a fix"],
  ["REVIEW", "Review"],
  ["AUTO_RESOLVED", "Auto-matched"],
  ["ALL", "Everything"],
];

export default function Queue() {
  const nav = useNavigate();
  const { id } = useParams();
  const [sp, setSp] = useSearchParams();
  const bucket = sp.get("bucket") || "ACTION";
  const sev = sp.get("severity") || "ALL";
  const status = sp.get("status") || "ALL";
  const type = sp.get("type") || "ALL";
  const sort = sp.get("sort") || "priority";
  const q = sp.get("q") || "";

  const { data, updateItem: setData, isLoading: loading, error, refetch: reload } = useQueue();
  const [fallback, setFallback] = useState<QueueItem | null>(null);
  const [sel, setSel] = useState(0);

  function setParam(k: string, v: string, def: string) {
    const next = new URLSearchParams(sp);
    if (!v || v === def) next.delete(k);
    else next.set(k, v);
    setSp(next, { replace: true });
  }

  const items = data ?? [];
  const types = useMemo(() => Array.from(new Set(items.map((i) => i.issue_type))).sort(), [items]);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let r = items.filter((i) => {
      if (bucket === "ACTION" && !(i.bucket === "AT_RISK" || i.bucket === "NEEDS_FIX")) return false;
      if (bucket !== "ACTION" && bucket !== "ALL" && i.bucket !== bucket) return false;
      if (sev !== "ALL" && i.severity !== sev) return false;
      if (status !== "ALL" && i.status !== status) return false;
      if (type !== "ALL" && i.issue_type !== type) return false;
      if (needle) {
        const hay = `${supplierName(i)} ${invoiceLabel(i)} ${i.title} ${i.issue_type}`.toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
    r = [...r].sort((a, b) => {
      if (sort === "amount") return b.amount_at_stake - a.amount_at_stake;
      if (sort === "deadline") return (a.deadline || "9999").localeCompare(b.deadline || "9999");
      return b.priority_score - a.priority_score;
    });
    return r;
  }, [items, bucket, sev, status, type, sort, q]);

  const total = rows.reduce((s, r) => s + (r.amount_at_stake || 0), 0);
  const selected = id ? items.find((i) => String(i.id) === id) ?? (fallback && String(fallback.id) === id ? fallback : null) : null;

  useEffect(() => {
    if (id && !loading && !items.find((i) => String(i.id) === id)) {
      api.queueItem(id).then(setFallback).catch(() => undefined);
    }
  }, [id, loading, items]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (e.key === "Escape" && id) nav({ pathname: "/queue", search: sp.toString() });
      else if (!id && e.key === "ArrowDown") setSel((s) => Math.min(s + 1, rows.length - 1));
      else if (!id && e.key === "ArrowUp") setSel((s) => Math.max(s - 1, 0));
      else if (!id && e.key === "Enter" && rows[sel]) nav({ pathname: `/queue/${rows[sel].id}`, search: sp.toString() });
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [id, rows, sel, sp, nav]);

  function update(it: QueueItem) {
    setData(it);
    if (fallback && fallback.id === it.id) setFallback(it);
  }

  if (loading && !data) return <Loading label="Turning the ledger pages..." />;
  if (error) return <ErrorBox error={error} onRetry={reload} />;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Recovery Queue</h1>
          <p className="sub">Every problem with what it costs, why, and the next step. Highest priority first.</p>
        </div>
      </div>

      <div className="filters sheet">
        <label>Show
          <select value={bucket} onChange={(e) => setParam("bucket", e.target.value, "ACTION")}>
            {BUCKET_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Issue
          <select value={type} onChange={(e) => setParam("type", e.target.value, "ALL")}>
            <option value="ALL">All types</option>
            {types.map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}
          </select>
        </label>
        <label>Severity
          <select value={sev} onChange={(e) => setParam("severity", e.target.value, "ALL")}>
            <option value="ALL">All</option>
            {Object.entries(SEVERITY_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </label>
        <label>Status
          <select value={status} onChange={(e) => setParam("status", e.target.value, "ALL")}>
            <option value="ALL">All</option>
            {["OPEN", "ACTIONED", "RESOLVED", "DISMISSED"].map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
          </select>
        </label>
        <label>Sort
          <select value={sort} onChange={(e) => setParam("sort", e.target.value, "priority")}>
            <option value="priority">Priority</option>
            <option value="amount">Amount</option>
            <option value="deadline">Deadline</option>
          </select>
        </label>
        <label className="grow">Search
          <input value={q} placeholder="Supplier, invoice or issue" onChange={(e) => setParam("q", e.target.value, "")} />
        </label>
      </div>

      <div className="sumrow">
        <b>{rows.length}</b> issues &middot; <b>{formatINR(total)}</b> at stake
      </div>

      {rows.length === 0 ? (
        <Empty text="Nothing needs attention for this filter." />
      ) : (
        <div className="sheet table-sheet">
          <table className="qt">
            <thead>
              <tr>
                <th>#</th>
                <th>Supplier and issue</th>
                <th className="num">At stake</th>
                <th>Deadline</th>
                <th>Next step</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={r.id}
                  className={i === sel ? "sel" : ""}
                  onClick={() => nav({ pathname: `/queue/${r.id}`, search: sp.toString() })}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && nav({ pathname: `/queue/${r.id}`, search: sp.toString() })}
                >
                  <td className="rank">{i + 1}</td>
                  <td>
                    <div className="t1">{r.title || titleCase(r.issue_type)}</div>
                    <div className="t2">
                      {supplierName(r)}
                      {invoiceLabel(r) && <> &middot; {invoiceLabel(r)}</>}
                      {r.entity?.invoice_date && <> &middot; {formatDate(r.entity.invoice_date)}</>}
                    </div>
                  </td>
                  <td className="num strong">{formatINR(r.amount_at_stake)}</td>
                  <td>
                    {r.deadline ? (
                      <>
                        <div>{formatDate(r.deadline)}</div>
                        <div className={"dl " + (r.days_left !== null && r.days_left <= 7 ? "hot" : "")}>{daysLeftLabel(r.days_left)}</div>
                      </>
                    ) : (
                      <span className="muted">-</span>
                    )}
                  </td>
                  <td><Badge tone={bucketTone(r.bucket)}>{ACTION_LABEL[r.recommended_action] ?? r.recommended_action}</Badge></td>
                  <td><span className={"st " + r.status.toLowerCase()}>{titleCase(r.status)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <Drawer item={selected} onClose={() => nav({ pathname: "/queue", search: sp.toString() })} onChange={update} />
      )}
      {!selected && id && !loading && <div className="muted pad">Looking for issue #{id}...</div>}
    </div>
  );
}
