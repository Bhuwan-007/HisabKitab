import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ForceGraph2D from "react-force-graph-2d";
import { api } from "../api";
import { ErrorBox, Loading, Empty, Badge } from "../components/ui";
import { formatINR } from "../format";

function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(score * 100)));
  const color = pct > 60 ? "var(--risk)" : pct > 30 ? "var(--fix)" : "var(--safe)";
  return (
    <div style={{ width: 100, background: "#e5e5e5", height: 8, borderRadius: 4, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, background: color, height: "100%" }} />
    </div>
  );
}

function SupplierDrawer({ id, onClose }: { id: number; onClose: () => void }) {
  const { data: d, isLoading, error, refetch } = useQuery({
    queryKey: ["supplier", id],
    queryFn: () => api.supplier(id)
  });

  if (isLoading) return <div className="drawer open"><div className="drawer-in"><Loading label="Loading..." /></div></div>;
  if (error) return <div className="drawer open"><div className="drawer-in"><ErrorBox error={error as Error} onRetry={refetch} /></div></div>;
  if (!d) return null;

  return (
    <div className="drawer open">
      <div className="drawer-in">
        <div className="d-head">
          <button className="close" onClick={onClose}>&times;</button>
          <h2>{d.name}</h2>
          <div className="sub">GSTIN: {d.gstin}</div>
        </div>

        <div className="d-body">
          <div className="sheet">
            <h3>Risk Profile</h3>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <strong style={{ fontSize: "1.5rem" }}>{Math.round(d.score * 100)} / 100</strong>
              <ScoreBar score={d.score} />
            </div>
            
            <h4>Top Factors</h4>
            {d.factors && Object.entries(d.factors).map(([k, v]: [string, any]) => (
              <div key={k} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: 4 }}>
                  <span>{k.replace(/_/g, " ")}</span>
                  <span>{Math.round(v * 100)}%</span>
                </div>
                <ScoreBar score={v} />
              </div>
            ))}
          </div>

          <div className="sheet">
            <h3>Open Issues</h3>
            {d.issues && d.issues.length > 0 ? (
              <ul style={{ paddingLeft: 16 }}>
                {d.issues.map((iss: any) => (
                  <li key={iss.id} style={{ marginBottom: 8 }}>
                    <strong>{iss.title}</strong>
                    <div className="sub">{iss.plain_reason}</div>
                  </li>
                ))}
              </ul>
            ) : <Empty text="No open issues." />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Suppliers() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: suppliers, isLoading: supLoading, error: supError, refetch: supReload } = useQuery({
    queryKey: ["suppliers"],
    queryFn: () => api.suppliers()
  });

  const { data: graphData, isLoading: gLoading, error: gError } = useQuery({
    queryKey: ["graph"],
    queryFn: () => api.graph()
  });

  const sorted = suppliers ? [...suppliers].sort((a, b) => b.score - a.score) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div className="page-head">
        <div>
          <h1>Suppliers & Counterparty Network</h1>
          <p className="sub">Identify high-risk suppliers and simulated network cycles.</p>
        </div>
      </div>

      <div className="spread">
        <section className="sheet page-l" style={{ overflowX: "auto" }}>
          <h3>Top Risky Suppliers</h3>
          {supLoading && <Loading label="Loading suppliers..." />}
          {supError && <ErrorBox error={supError as Error} onRetry={supReload} />}
          {sorted.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>GSTIN</th>
                  <th>Score</th>
                  <th>Top Factor</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(s => (
                  <tr key={s.id}>
                    <td>{s.name}</td>
                    <td className="sub">{s.gstin}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {Math.round(s.score * 100)}
                        <ScoreBar score={s.score} />
                      </div>
                    </td>
                    <td className="sub">{s.top_factor || "-"}</td>
                    <td>
                      <button className="btn small" onClick={() => setSelectedId(s.id)}>View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="sheet page-r" style={{ display: "flex", flexDirection: "column" }}>
          <h3 style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Simulated counterparty network</span>
          </h3>
          {gLoading && <Loading label="Loading graph..." />}
          {gError && <div className="bad">Failed to load graph</div>}
          {graphData && (
            <div style={{ flex: 1, minHeight: 400, border: "1px solid var(--border)", position: "relative" }}>
              <ForceGraph2D
                graphData={graphData}
                nodeAutoColorBy="group"
                nodeLabel="name"
                nodeRelSize={6}
                linkColor={(link: any) => link.is_cycle ? "var(--risk)" : "#999"}
                linkWidth={(link: any) => link.is_cycle ? 2 : 1}
                nodeColor={(node: any) => node.is_supplier ? "var(--primary)" : (node.in_cycle ? "var(--risk)" : "#ccc")}
              />
            </div>
          )}
          {graphData?.cycles && graphData.cycles.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4>Detected Cycles</h4>
              <ul style={{ paddingLeft: 16, margin: 0 }}>
                {graphData.cycles.map((c: any, i: number) => (
                  <li key={i}>
                    <strong>Cycle {i+1}:</strong> {formatINR(c.value)} <Badge tone="risk">needs review</Badge>
                    <div className="sub" style={{ fontSize: "0.8rem" }}>{c.nodes.join(" → ")}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
      
      {selectedId && <SupplierDrawer id={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}
