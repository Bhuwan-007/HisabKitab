import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Queue from "./pages/Queue";
import Audit from "./pages/Audit";
import Floating from "./components/Floating";

export default function App() {
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
            <NavLink to="/" end>📖 Ledger Book (Dashboard)</NavLink>
            <NavLink to="/queue">📋 Invoices & Queue</NavLink>
            <NavLink to="/audit">⚖️ Audit Trail & GST</NavLink>
          </nav>
          <div className="nav-actions">
            <div className="bookmark-ribbon">🔖 FY 2025-26 Q4</div>
            <button className="btn primary run-recon-btn">
              <span>⚡</span> Run Reconciliation
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/queue" element={<Queue />} />
          <Route path="/queue/:id" element={<Queue />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
      <footer className="foot">
        Prototype with synthetic data. Tax rules are simplified and rates are illustrative. Not tax or legal advice.
      </footer>
    </div>
  );
}
