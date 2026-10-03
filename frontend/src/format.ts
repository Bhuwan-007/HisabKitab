export function formatINR(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  const neg = n < 0;
  const abs = Math.abs(n);
  const whole = Number.isInteger(abs) || abs >= 1000;
  const fixed = whole ? Math.round(abs).toString() : abs.toFixed(2);
  const [intPart, dec] = fixed.split(".");
  let out = intPart;
  if (intPart.length > 3) {
    const last3 = intPart.slice(-3);
    const rest = intPart.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",");
    out = rest + "," + last3;
  }
  return (neg ? "-" : "") + "\u20B9" + out + (dec ? "." + dec : "");
}

export function formatLakh(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1e7) return `${sign}\u20B9${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}\u20B9${(abs / 1e5).toFixed(1)} L`;
  return formatINR(n);
}

export function formatDate(d: string | null | undefined): string {
  if (!d) return "";
  const dt = new Date(d.length === 10 ? d + "T00:00:00" : d);
  if (Number.isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function daysLeftLabel(n: number | null | undefined): string {
  if (n === null || n === undefined) return "";
  if (n < 0) return `${-n} days overdue`;
  if (n === 0) return "due today";
  if (n === 1) return "1 day left";
  return `${n} days left`;
}

export const ACTION_LABEL: Record<string, string> = {
  CHASE_SUPPLIER: "Chase supplier",
  HOLD_PAYMENT: "Hold payment",
  PAY_NOW: "Pay now",
  REVERSE_ITC: "Reverse credit",
  ASK_CREDIT_NOTE: "Ask for credit note",
  CORRECT_BOOKS: "Correct books",
  REMOVE_DUPLICATE: "Remove duplicate",
  RECORD_INVOICE: "Record invoice",
  INVESTIGATE: "Investigate",
  NO_ACTION: "No action",
};

export const BUCKET_LABEL: Record<string, string> = {
  AT_RISK: "At risk",
  NEEDS_FIX: "Needs a fix",
  REVIEW: "Review",
  AUTO_RESOLVED: "Auto-matched",
};

export const SEVERITY_LABEL: Record<string, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

const WORDS: Record<string, string> = { gstr2b: "GSTR-2B", gstin: "GSTIN", upi: "UPI", mdr: "MDR", itc: "ITC", gst: "GST" };

export function titleCase(s: string): string {
  return s
    .toLowerCase()
    .split("_")
    .map((w) => WORDS[w] ?? w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function bucketTone(b: string): string {
  if (b === "AT_RISK") return "risk";
  if (b === "NEEDS_FIX") return "fix";
  return "review";
}
