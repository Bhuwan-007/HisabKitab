import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { ErrorBox, Loading, Empty, Badge } from "../components/ui";
import { formatINR, titleCase } from "../format";

const SOURCES = [
  { id: "purchase_books", label: "Purchase Books" },
  { id: "gstr2b", label: "GSTR-2B" },
  { id: "sales_invoices", label: "Sales Invoices" },
  { id: "bank_transactions", label: "Bank" },
];

const STATUSES = ["MATCHED", "MATCHED_ADJUSTED", "DISCREPANT", "UNMATCHED", "DUPLICATE"];

export default function ReconExplorer() {
  const [source, setSource] = useState(SOURCES[0].id);
  const [status, setStatus] = useState("DISCREPANT");
  const [page, setPage] = useState(1);

  const { data: statusData, isLoading: sLoading, error: sError, refetch: sReload } = useQuery({
    queryKey: ["recordStatus"],
    queryFn: () => api.recordStatus()
  });

  const { data: records, isLoading: rLoading, error: rError, refetch: rReload } = useQuery({
    queryKey: ["records", source, status, page],
    queryFn: () => api.records(source, status, page)
  });

  if (sLoading && !statusData) return <Loading label="Loading sources..." />;
  if (sError) return <ErrorBox error={sError as Error} onRetry={sReload} />;

  const counts = statusData ? statusData[source] : {};

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Reconciliation Explorer</h1>
          <p className="sub">Inspect individual records and exactly how they matched.</p>
        </div>
      </div>

      <div className="tabs">
        {SOURCES.map((s) => (
          <button
            key={s.id}
            className={source === s.id ? "active" : ""}
            onClick={() => {
              setSource(s.id);
              setPage(1);
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="sheet">
        <div className="filters" style={{ marginBottom: 16 }}>
          {STATUSES.map((st) => (
            <button
              key={st}
              className={`chip ${status === st ? "active" : ""}`}
              onClick={() => {
                setStatus(st);
                setPage(1);
              }}
            >
              {titleCase(st.replace("_", " "))} ({counts ? (counts[st.toLowerCase()] ?? 0) : 0})
            </button>
          ))}
        </div>

        {rLoading && !records ? (
          <Loading label="Loading records..." />
        ) : rError ? (
          <ErrorBox error={rError as Error} onRetry={rReload} />
        ) : records && records.items.length === 0 ? (
          <Empty text="No records found for this status." />
        ) : (
          <div>
            <table className="qt">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th className="num">Amount</th>
                  <th>Counterpart Summary</th>
                  <th>Differences</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {records?.items.map((r: any) => (
                  <tr key={r.id}>
                    <td>#{r.id}</td>
                    <td className="num">{r.data?.total_amount ? formatINR(r.data.total_amount) : "-"}</td>
                    <td>{r.data?.counterpart_summary || "-"}</td>
                    <td className="diffs" style={{ color: "var(--risk)" }}>{r.data?.differences || "-"}</td>
                    <td>
                      {r.status === "DISCREPANT" && r.data?.issue_id && (
                        <Link to={`/queue/${r.data.issue_id}`} className="btn small">
                          View Issue
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Prev
              </button>
              <span>Page {page}</span>
              <button disabled={records && records.items.length < (records.page_size || 50)} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
