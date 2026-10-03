import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../api";
import { ErrorBox, Loading } from "../components/ui";

export default function Rules() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["rules"],
    queryFn: () => api.rules()
  });

  const [toast, setToast] = useState<{ msg: string; err?: boolean } | null>(null);

  const regen = useMutation({
    mutationFn: () => api.regenerate(),
    onSuccess: () => setToast({ msg: "Sample data regenerated successfully." }),
    onError: (e: any) => setToast({ msg: e.message, err: true })
  });

  const runRecon = useMutation({
    mutationFn: () => api.runRecon(),
    onSuccess: (d) => setToast({ msg: `Reconciliation complete. Found ${d.counts?.issues || 0} issues.` }),
    onError: (e: any) => setToast({ msg: e.message, err: true })
  });

  function handleRegen() {
    if (confirm("Are you sure you want to regenerate all sample data? This will overwrite the current database.")) {
      regen.mutate();
    }
  }

  function handleRun() {
    runRecon.mutate();
  }

  if (isLoading) return <Loading label="Loading rules..." />;
  if (error) return <ErrorBox error={error as Error} onRetry={refetch} />;

  const { active_config, rate_table } = data || {};

  return (
    <div style={{ paddingBottom: 64 }}>
      <div className="page-head">
        <div>
          <h1>Rules & Configuration</h1>
          <p className="sub">GST rates, thresholds, and manual triggers.</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <button className="btn" onClick={handleRegen} disabled={regen.isPending}>
          {regen.isPending ? "Generating..." : "Regenerate sample data"}
        </button>
        <button className="btn primary" onClick={handleRun} disabled={runRecon.isPending}>
          {runRecon.isPending ? "Running..." : "Run reconciliation"}
        </button>
      </div>

      {toast && (
        <div className={`note ${toast.err ? "bad" : "ok"}`} style={{ marginBottom: 24 }}>
          {toast.msg}
          <button className="close" onClick={() => setToast(null)}>&times;</button>
        </div>
      )}

      <div className="spread">
        <section className="sheet page-l">
          <h3>Active Configuration</h3>
          <table className="table">
            <tbody>
              {active_config && Object.entries(active_config).map(([k, v]) => (
                <tr key={k}>
                  <td><strong>{k}</strong></td>
                  <td>{String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="sheet page-r">
          <h3>Rate Table</h3>
          <div className="note" style={{ marginBottom: 16 }}>
            <strong>Note:</strong> Some items changed rates on 22 Sep 2025 (e.g. Namkeen). The engine enforces the rate based on the invoice date.
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>HSN</th>
                <th>Description</th>
                <th>Before</th>
                <th>After</th>
              </tr>
            </thead>
            <tbody>
              {rate_table?.map((r: any) => (
                <tr key={r.hsn}>
                  <td>{r.hsn}</td>
                  <td>{r.description}</td>
                  <td>{r.rate_before}%</td>
                  <td>{r.rate_after}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
