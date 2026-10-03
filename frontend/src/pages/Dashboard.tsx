import { Link, useSearchParams } from "react-router-dom";
import { api, useSummary } from "../api";
import { ACTION_LABEL, bucketTone, daysLeftLabel, formatDate, formatINR, formatLakh } from "../format";
import { ErrorBox, Loading, Badge } from "../components/ui";
import Donut from "../components/Donut";
import { invoiceLabel, supplierName } from "../components/Drawer";
import { useQuery } from "@tanstack/react-query";
import type { QueueItem } from "../types";

function monthOptions(asOf?: string): string[] {
  const base = asOf ? new Date(asOf + "T00:00:00") : new Date();
  const out: string[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(base.getFullYear(), base.getMonth() - i, 1);
    out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  return out;
}

export default function Dashboard() {
  const [sp, setSp] = useSearchParams();
  const period = sp.get("period") || undefined;
  
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health()
  });
  
  const { data: s, isLoading: sumLoading, error: sumError, refetch: sumReload } = useSummary(period);

  if (sumLoading && !s) return <Loading label="Opening the books..." />;
  if (sumError) return <ErrorBox error={sumError as Error} onRetry={sumReload} />;
  
  if (!s) return null;
  const L = s.liability;
  const shownPeriod = period || healthData?.period || "";

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="sub">
            Before you file: what is safe to claim, what is at risk, and what to fix.
            {healthData && <> As of {formatDate(healthData.as_of_date)}.</>}
          </p>
        </div>
        <label className="period">
          Tax period
          <select value={shownPeriod} onChange={(e) => setSp(e.target.value ? { period: e.target.value } : {})}>
            {!shownPeriod && <option value="">Current</option>}
            {monthOptions(healthData?.as_of_date).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="kpis">
        <Link to="/queue?bucket=ALL" className="kpi safe sheet" title="ITC with no open issue">
          <span className="kpi-label"><i className="ico">{"\u2713"}</i> Safe to claim</span>
          <strong>{formatLakh(s.safe_to_claim)}</strong>
          <span className="kpi-hint">{formatINR(s.safe_to_claim)} of tax credit with no open issue</span>
        </Link>
        <Link to="/queue?bucket=AT_RISK" className="kpi risk sheet" title="Depends on a supplier or the government">
          <span className="kpi-label"><i className="ico">!</i> At risk</span>
          <strong>{formatLakh(s.at_risk)}</strong>
          <span className="kpi-hint">Could be blocked or reversed</span>
        </Link>
        <Link to="/queue?bucket=NEEDS_FIX" className="kpi fix sheet" title="Can be corrected by us or the supplier">
          <span className="kpi-label"><i className="ico">{"\u270E"}</i> Needs a fix</span>
          <strong>{formatLakh(s.needs_fix)}</strong>
          <span className="kpi-hint">Wrong rate, duplicate, typo and similar</span>
        </Link>
      </div>

      <div className="spread">
        <section className="sheet page-l">
          <h3>Reconciliation status</h3>
          <Donut data={s.status_breakdown as any} />
          <p className="strip">
            {s.status_breakdown.matched_adjusted ?? 0} records were matched automatically after a rounding or UPI fee
            difference. Those are explained, not errors.
          </p>
        </section>

        <section className="sheet page-r">
          <h3>Tax liability estimate</h3>
          <table className="liab">
            <tbody>
              <tr><td>Output tax (on sales)</td><td className="num">{formatINR(L.output_tax)}</td></tr>
              <tr><td>Credit you can claim now</td><td className="num">{formatINR(L.itc_claim_now)}</td></tr>
              <tr className="em"><td>Net payable now</td><td className="num">{formatINR(L.net_payable_now)}</td></tr>
              <tr><td>Credit if every issue is recovered</td><td className="num">{formatINR(L.itc_if_all_recovered)}</td></tr>
              <tr><td>Net payable if all recovered</td><td className="num">{formatINR(L.net_payable_if_recovered)}</td></tr>
              <tr className="total"><td>Cash impact of open issues</td><td className="num">{formatINR(L.cash_impact_of_issues)}</td></tr>
            </tbody>
          </table>
          <p className="fine">Simplified: single registration, no opening balance, no reverse charge.</p>

          <h3 className="top-h">Top to act on</h3>
          {s.top5_queue.length === 0 && <div className="empty">Nothing needs attention.</div>}
          <ol className="top5">
            {s.top5_queue.map((q: QueueItem) => (
              <li key={q.id}>
                <Link to={`/queue/${q.id}`}>
                  <div className="t-main">
                    <b>{formatINR(q.amount_at_stake)}</b>
                    <span>{q.title}</span>
                    <small>{supplierName(q)} {invoiceLabel(q) && <>&middot; {invoiceLabel(q)}</>}</small>
                  </div>
                  <div className="t-side">
                    <Badge tone={bucketTone(q.bucket)}>{ACTION_LABEL[q.recommended_action] ?? q.recommended_action}</Badge>
                    {q.deadline && <small>{formatDate(q.deadline)} &middot; {daysLeftLabel(q.days_left)}</small>}
                  </div>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
