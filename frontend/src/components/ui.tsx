import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

export function Badge({ tone, children }: { tone: string; children: ReactNode }) {
  return <span className={`chip ${tone}`}>{children}</span>;
}

const EQUATIONS = [
  { rows: ["\u20B9 1,80,000", "+ \u20B9 92,000", "+ \u20B9 38,400"], total: "\u20B9 3,10,400", note: "Adding up what is at stake..." },
  { rows: ["\u20B9 3,000", "\u00D7 0.4% fee"], total: "\u20B9 12", note: "Working out the UPI fee..." },
  { rows: ["180 days", "\u2212 169 days used"], total: "11 days left", note: "Counting the 180-day clock..." },
];

export function Loading({ label }: { label?: string }) {
  const [show, setShow] = useState(false);
  const eq = useMemo(() => EQUATIONS[Math.floor(Math.random() * EQUATIONS.length)], []);
  useEffect(() => {
    const t = setTimeout(() => setShow(true), 300);
    return () => clearTimeout(t);
  }, []);
  if (!show) return <div className="loading-gap" />;
  return (
    <div className="eq-wrap" role="status" aria-live="polite">
      <div className="eq">
        {eq.rows.map((r, i) => (
          <div key={i} className="eq-row" style={{ animationDelay: `${i * 0.45}s` }}>
            {r}
          </div>
        ))}
        <div className="eq-row eq-total" style={{ animationDelay: `${eq.rows.length * 0.45 + 0.2}s` }}>
          {eq.total}
        </div>
      </div>
      <div className="eq-note">{label || eq.note}</div>
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="sheet error-box" role="alert">
      <h3>Something went wrong</h3>
      <p>{error.message}</p>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function Empty({ text }: { text: string }) {
  return <div className="empty">{text}</div>;
}
