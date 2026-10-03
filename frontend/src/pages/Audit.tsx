import { useState } from "react";
import { api, useAsync } from "../api";
import { ErrorBox, Loading, Empty } from "../components/ui";
import { titleCase } from "../format";

const MONEY_TYPES = [
  "MISSING_IN_GSTR2B", "SUPPLIER_GSTIN_CANCELLED", "PAYMENT_180_DAY_RISK", "AMOUNT_MISMATCH", "WRONG_TAX_RATE",
  "WRONG_TAX_TYPE", "DUPLICATE_INVOICE", "MISSING_IN_BOOKS", "UPI_MDR_ADJUSTED", "UPI_SHORT_SETTLEMENT_UNEXPLAINED",
  "UNMATCHED_PAYMENT", "UNMATCHED_RECEIPT", "ROUNDING_DIFF",
];

function pct(n: number) {
  return Math.round(n * 100) + "%";
}

export default function Audit() {
  const ev = useAsync(() => api.evaluation(), []);
  const au = useAsync(() => api.audit(), []);
  const [ver, setVer] = useState<string | null>(null);
  const [verBad, setVerBad] = useState(false);

  async function verify() {
    setVer("Checking...");
    try {
      const r = await api.verify();
      setVerBad(!r.valid);
      setVer(r.valid ? "Chain is valid. No record has been altered." : `Chain broken at record #${r.broken_at_id}.`);
    } catch (e: any) {
      setVerBad(true);
      setVer(e.message);
    }
  }

  const metrics = ev.data ?? {};
  const keys = Object.keys(metrics);
  const money = keys.filter((k) => MONEY_TYPES.includes(k));
  const review = keys.filter((k) => !MONEY_TYPES.includes(k));

  const Row = ({ k }: { k: string }) => {
    const m = metrics[k];
    return (
      <tr>
        <td>{titleCase(k)}</td>
        <td className={"num " + (m.precision < 0.7 ? "bad" : "")}>{pct(m.precision)}</td>
        <td className={"num " + (m.recall < 0.7 ? "bad" : "")}>{pct(m.recall)}</td>
      </tr>
    );
  };

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Audit trail and accuracy</h1>
          <p className="sub">Proof of when each problem was caught, and how well the checks perform.</p>
        </div>
      </div>

      <div className="two">
        <section className="sheet">
          <h3>Tamper-evident audit trail</h3>
          <button className="btn primary" onClick={verify}>Verify chain</button>
          {ver && <div className={"verdict " + (verBad ? "bad" : "ok")}>{verBad ? "\u2717 " : "\u2713 "}{ver}</div>}
          {au.loading && <Loading label="Reading the log..." />}
          {au.error && <ErrorBox error={au.error} onRetry={au.reload} />}
          {au.data && au.data.length === 0 && <Empty text="No audit entries yet. Run a reconciliation first." />}
          {au.data && au.data.length > 0 && (
            <table className="audit">
              <thead><tr><th>When</th><th>Who</th><th>What</th><th>Record</th></tr></thead>
              <tbody>
                {au.data.slice(0, 30).map((r: any, i: number) => (
                  <tr key={r.id ?? i}>
                    <td>{String(r.ts ?? "").replace("T", " ").slice(0, 19)}</td>
                    <td>{r.actor}</td>
                    <td>{titleCase(String(r.action ?? ""))}</td>
                    <td>{r.entity_type}{r.entity_id ? ` #${r.entity_id}` : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="sheet">
          <h3>Detection accuracy</h3>
          <p className="fine">Measured on errors we planted in the synthetic data. Not a real-world accuracy claim.</p>
          {ev.loading && <Loading label="Checking the answers..." />}
          {ev.error && <ErrorBox error={ev.error} onRetry={ev.reload} />}
          {ev.data && (
            <>
              <h4>Money rules</h4>
              <table className="audit"><thead><tr><th>Check</th><th className="num">Precision</th><th className="num">Recall</th></tr></thead>
                <tbody>{money.map((k) => <Row key={k} k={k} />)}</tbody></table>
              <h4>Review signals (flag for a human, so noisier by design)</h4>
              <table className="audit"><thead><tr><th>Check</th><th className="num">Precision</th><th className="num">Recall</th></tr></thead>
                <tbody>{review.map((k) => <Row key={k} k={k} />)}</tbody></table>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
