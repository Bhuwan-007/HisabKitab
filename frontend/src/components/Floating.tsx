export default function Floating() {
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  return (
    <div className="floaters" aria-hidden="true">
      <span className="fl f1 rupee">{"\u20B9"}</span>
      <svg className="fl f2" width="90" height="90" viewBox="0 0 80 80" {...stroke}>
        <ellipse cx="40" cy="62" rx="26" ry="9" />
        <path d="M14 62v-10M66 62v-10" />
        <ellipse cx="40" cy="52" rx="26" ry="9" />
        <path d="M14 52v-10M66 52v-10" />
        <ellipse cx="40" cy="42" rx="26" ry="9" />
        <path d="M14 42v-10M66 42v-10" />
        <ellipse cx="40" cy="32" rx="26" ry="9" />
      </svg>
      <svg className="fl f3" width="110" height="90" viewBox="0 0 110 90" {...stroke}>
        <path d="M8 8v74h98" />
        <path d="M18 66l22-22 18 12 30-38" />
        <path d="M80 18h12v12" />
      </svg>
      <svg className="fl f4" width="100" height="80" viewBox="0 0 100 80" {...stroke}>
        <rect x="6" y="6" width="88" height="68" rx="4" />
        <path d="M6 24h88M30 6v68M18 38h6M18 50h6M18 62h6M40 38h44M40 50h44M40 62h30" />
      </svg>
      <svg className="fl f5" width="100" height="90" viewBox="0 0 100 90" {...stroke}>
        <rect x="6" y="6" width="88" height="78" rx="4" />
        <path d="M6 28h88M6 52h88M30 6v78M50 6v78M70 6v78" />
        <circle cx="18" cy="17" r="5" />
        <circle cx="40" cy="40" r="5" />
        <circle cx="60" cy="63" r="5" />
        <circle cx="82" cy="40" r="5" />
      </svg>
      <svg className="fl f6" width="100" height="90" viewBox="0 0 100 90" {...stroke}>
        <path d="M50 8v66M30 74h40M16 24h68" />
        <path d="M16 24l-10 28h20z" />
        <path d="M84 24l-10 28h20z" />
      </svg>
      <span className="fl f7 rupee">{"\u20B9"}</span>
      <svg className="fl f8" width="80" height="80" viewBox="0 0 80 80" {...stroke}>
        <circle cx="40" cy="40" r="30" />
        <circle cx="40" cy="40" r="22" />
        <path d="M28 40h24M40 28v24" />
      </svg>
    </div>
  );
}
