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
        <div className="brand">
          <span className="logo">{"\u20B9"}</span>
          <div>
            <div className="brand-name">ITC Shield</div>
            <div className="brand-sub">Hisab-Kitab, before you file</div>
          </div>
        </div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/queue">Recovery Queue</NavLink>
          <NavLink to="/audit">Audit and accuracy</NavLink>
        </nav>
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
