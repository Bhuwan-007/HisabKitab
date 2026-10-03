const ORDER = ["matched", "matched_adjusted", "discrepant", "unmatched", "duplicate"] as const;
const LABEL: Record<string, string> = {
  matched: "Matched",
  matched_adjusted: "Matched after rounding or UPI fee",
  discrepant: "Discrepant",
  unmatched: "Unmatched",
  duplicate: "Duplicate",
};
const FILL: Record<string, string> = {
  matched: "#3B2416",
  matched_adjusted: "url(#h-diag)",
  discrepant: "#B28A33",
  unmatched: "url(#h-cross)",
  duplicate: "url(#h-dots)",
};

function polar(cx: number, cy: number, r: number, a: number) {
  const rad = ((a - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

function slice(cx: number, cy: number, ro: number, ri: number, a0: number, a1: number) {
  const large = a1 - a0 > 180 ? 1 : 0;
  const [x0, y0] = polar(cx, cy, ro, a0);
  const [x1, y1] = polar(cx, cy, ro, a1);
  const [x2, y2] = polar(cx, cy, ri, a1);
  const [x3, y3] = polar(cx, cy, ri, a0);
  return `M${x0} ${y0} A${ro} ${ro} 0 ${large} 1 ${x1} ${y1} L${x2} ${y2} A${ri} ${ri} 0 ${large} 0 ${x3} ${y3} Z`;
}

export function Patterns() {
  return (
    <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
      <defs>
        <pattern id="h-diag" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)">
          <rect width="7" height="7" fill="#F2E6CC" />
          <line x1="0" y1="0" x2="0" y2="7" stroke="#231710" strokeWidth="2.4" />
        </pattern>
        <pattern id="h-cross" patternUnits="userSpaceOnUse" width="7" height="7">
          <rect width="7" height="7" fill="#F2E6CC" />
          <path d="M0 0L7 7M7 0L0 7" stroke="#A3271F" strokeWidth="1.6" />
        </pattern>
        <pattern id="h-dots" patternUnits="userSpaceOnUse" width="6" height="6">
          <rect width="6" height="6" fill="#F2E6CC" />
          <circle cx="3" cy="3" r="1.8" fill="#6B1F2A" />
        </pattern>
      </defs>
    </svg>
  );
}

export default function Donut({ data }: { data: Record<string, number> }) {
  const items = ORDER.map((k) => ({ key: k, value: Number(data[k] ?? 0) }));
  const total = items.reduce((s, i) => s + i.value, 0);
  let angle = 0;
  const cx = 90, cy = 90, ro = 80, ri = 50;
  return (
    <div className="donut-wrap">
      <Patterns />
      <svg width="180" height="180" viewBox="0 0 180 180" role="img" aria-label="Reconciliation status breakdown">
        {total === 0 && <circle cx={cx} cy={cy} r={(ro + ri) / 2} fill="none" stroke="#D8BC8E" strokeWidth={ro - ri} />}
        {items.map((it) => {
          if (!it.value) return null;
          const sweep = (it.value / total) * 360;
          const a0 = angle;
          const a1 = angle + Math.min(sweep, 359.99);
          angle += sweep;
          return <path key={it.key} d={slice(cx, cy, ro, ri, a0, a1)} fill={FILL[it.key]} stroke="#F2E6CC" strokeWidth="2" />;
        })}
        <text x={cx} y={cy - 2} textAnchor="middle" className="donut-total">{total}</text>
        <text x={cx} y={cy + 16} textAnchor="middle" className="donut-sub">records</text>
      </svg>
      <ul className="legend">
        {items.map((it) => (
          <li key={it.key}>
            <svg width="22" height="14" aria-hidden="true">
              <rect width="22" height="14" rx="2" fill={FILL[it.key]} stroke="#231710" strokeWidth="1" />
            </svg>
            <span>{LABEL[it.key]}</span>
            <b>{it.value}</b>
          </li>
        ))}
      </ul>
    </div>
  );
}
