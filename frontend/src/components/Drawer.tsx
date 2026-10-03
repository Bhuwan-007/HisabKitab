import { useState } from "react";
import { api } from "../api";
import { ACTION_LABEL, BUCKET_LABEL, SEVERITY_LABEL, bucketTone, daysLeftLabel, formatDate, formatINR, titleCase } from "../format";
import type { QueueItem } from "../types";
import { Badge } from "./ui";

export function supplierName(it: QueueItem) {
  return it.entity?.supplier_name || (it.entity?.supplier_id ? `Supplier #${it.entity.supplier_id}` : "Unknown supplier");
}
export function invoiceLabel(it: QueueItem) {
  return it.entity?.invoice_no || (it.entity?.id ? `Invoice #${it.entity.id}` : "");
}

function pickText(r: any): string | null {
  if (!r) return null;
  if (typeof r === "string") return r;
  return r.explanation ?? r.text ?? r.message ?? null;
}

export default function Drawer({
  item,
  onClose,
  onChange,
}: {
  item: QueueItem;
  onClose: () => void;
  onChange: (it: QueueItem) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [stamp, setStamp] = useState(false);
  const [copied, setCopied] = useState(false);

  const draft: any = item.draft;
  const draftSubject = draft && typeof draft === "object" ? draft.subject : undefined;
  const draftBody = draft && typeof draft === "object" ? draft.body : typeof draft === "string" ? draft : undefined;

  async function explain() {
    setBusy("explain");
    setErr(null);
    try {
      const r = await api.explain(item.id);
      const text = pickText(r) ?? pickText(r?.item) ?? null;
      onChange({ ...item, explanation: text ?? item.plain_reason });
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  }

  async function makeDraft() {
    setBusy("draft");
    setErr(null);
    try {
      const r = await api.draft(item.id);
      const d = r?.draft ?? r;
      onChange({ ...item, draft: typeof d === "object" ? { subject: d.subject, body: d.body } : String(d) });
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  }

  async function setStatus(status: string) {
    const prev = item;
    onChange({ ...item, status });
    setErr(null);
    try {
      await api.setStatus(item.id, status);
      if (status === "RESOLVED") {
        setStamp(true);
        setTimeout(() => setStamp(false), 2600);
      }
    } catch (e: any) {
      onChange(prev);
      setErr(e.message);
    }
  }

  async function copy() {
    const text = (draftSubject ? `Subject: ${draftSubject}\n\n` : "") + (draftBody ?? "");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <>
      <div className="overlay" onClick={onClose} />
      <aside className="drawer sheet" role="dialog" aria-label="Issue details">
        {stamp && <div className="stamp">VERIFIED</div>}
        <button className="close" onClick={onClose} aria-label="Close">
          Esc
        </button>
        <div className="d-badges">
          <Badge tone={bucketTone(item.bucket)}>{BUCKET_LABEL[item.bucket] ?? item.bucket}</Badge>
          <Badge tone="plain">{SEVERITY_LABEL[item.severity] ?? item.severity}</Badge>
          <Badge tone="plain">{item.status}</Badge>
        </div>
        <h2>{item.title || titleCase(item.issue_type)}</h2>
        <div className="d-sub">
          {supplierName(item)} {invoiceLabel(item) && <>&middot; {invoiceLabel(item)}</>}
          {item.entity?.invoice_date && <> &middot; {formatDate(item.entity.invoice_date)}</>}
        </div>

        <div className="d-amount">
          <span>At stake</span>
          <strong>{formatINR(item.amount_at_stake)}</strong>
          {item.deadline && (
            <em>
              by {formatDate(item.deadline)} ({daysLeftLabel(item.days_left)})
            </em>
          )}
        </div>

        <p className="d-reason">{item.plain_reason}</p>
        <div className="d-action">
          Next step: <b>{ACTION_LABEL[item.recommended_action] ?? item.recommended_action}</b>
        </div>

        <h4>Evidence</h4>
        <table className="ev">
          <tbody>
            {item.evidence?.map((e, i) => (
              <tr key={i}>
                <td>{e.label}</td>
                <td className="num">{e.value}</td>
                <td className="src">{e.source}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h4>Why we flagged this</h4>
        <div className="why">
          Rule <b>{item.rule_id}</b> &middot; {titleCase(item.issue_type)} &middot; confidence {Math.round((item.confidence ?? 0) * 100)}%
        </div>

        <div className="d-btns">
          <button className="btn" onClick={explain} disabled={busy === "explain"}>
            {busy === "explain" ? "Writing..." : "Explain this"}
          </button>
          <button className="btn" onClick={makeDraft} disabled={busy === "draft"}>
            {busy === "draft" ? "Drafting..." : "Draft message"}
          </button>
        </div>

        {item.explanation && <div className="note">{item.explanation}</div>}

        {(draftSubject || draftBody) && (
          <div className="draft">
            {draftSubject && <div className="subj">Subject: {draftSubject}</div>}
            <pre>{draftBody}</pre>
            <button className="btn small" onClick={copy}>
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        )}

        <h4>Status</h4>
        <div className="d-btns">
          <button className="btn small" onClick={() => setStatus("ACTIONED")} disabled={item.status === "ACTIONED"}>
            Mark actioned
          </button>
          <button className="btn small primary" onClick={() => setStatus("RESOLVED")} disabled={item.status === "RESOLVED"}>
            Mark resolved
          </button>
          <button className="btn small" onClick={() => setStatus("DISMISSED")} disabled={item.status === "DISMISSED"}>
            Dismiss
          </button>
        </div>
        {err && <div className="err">{err}</div>}
      </aside>
    </>
  );
}
