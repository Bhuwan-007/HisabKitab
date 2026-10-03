import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Queue from "./pages/Queue";
import Audit from "./pages/Audit";
import ReconExplorer from "./pages/ReconExplorer";
import Rules from "./pages/Rules";
import Floating from "./components/Floating";
import { useMutation } from "@tanstack/react-query";
import { api } from "./api";

export default function App() {
  const nav = useNavigate();
  
  const runRecon = useMutation({
    mutationFn: () => api.runRecon(),
    onSuccess: () => {
      // Reload page or show success
      nav("/");
      window.location.reload();
    },
    onError: (e) => alert("Reconciliation failed: " + e.message)
  });

  return (
    <div className="app">
      <Floating />
      <header className="top">
        <div className="top-row">
          <div className="brand">
            <span className="logo">{"\u20B9"}</span>
            <div>
              <div className="brand-name">HisabKitab Ledger</div>
              <div className="brand-sub">Authenticated Vintage Ledger & GST Reconciliation</div>
            </div>
          </div>
          
          <div className="header-controls">
            <div className="ctrl-item">
              <span className="ctrl-lbl">Size:</span>
              <select className="ctrl-sel"><option>Dukaan</option><option>Vyapaar</option><option>Company</option></select>
            </div>
            <div className="ctrl-item">
              <span className="ctrl-lbl">Bhasha:</span>
              <button className="ctrl-btn">EN / हिंदी</button>
            </div>
            <div className="ctrl-item">
              <span className="ctrl-lbl">Role:</span>
              <select className="ctrl-sel"><option>Accountant</option><option>Owner</option><option>Auditor</option></select>
            </div>
          </div>
        </div>
        
        <div className="nav-row">
          <nav>
            <NavLink to="/" end>📖 Ledger Book</NavLink>
            <NavLink to="/queue">📋 Invoices & Queue</NavLink>
            <NavLink to="/reconciliation">🔍 Recon Explorer</NavLink>
            <NavLink to="/audit">⚖️ Audit Trail</NavLink>
            <NavLink to="/rules">⚙️ Rules</NavLink>
          </nav>
          <div className="nav-actions">
            <div className="bookmark-ribbon">🔖 FY 2026-27</div>
            <button className="btn primary run-recon-btn" onClick={() => runRecon.mutate()} disabled={runRecon.isPending}>
              <span>⚡</span> {runRecon.isPending ? "Running..." : "Run Reconciliation"}
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/queue" element={<Queue />} />
          <Route path="/queue/:id" element={<Queue />} />
          <Route path="/reconciliation" element={<ReconExplorer />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
      <footer className="foot">
        Prototype with synthetic data. Tax rules are simplified and rates are illustrative. Not tax or legal advice.
        Examples: The wrong-rate item ("invoice dated after 22 Sep 2025 still at the old rate"), the 180-day item, and the UPI fee deposit that is explained, not flagged.
      </footer>
    </div>
  );
}
