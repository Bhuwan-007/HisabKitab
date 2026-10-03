export type Evidence = { label: string; value: string; source?: string };

export type Entity = {
  type?: string | null;
  id?: number | null;
  invoice_no?: string | null;
  invoice_date?: string | null;
  supplier_id?: number | null;
  supplier_name?: string | null;
};

export type Draft = { subject?: string; body?: string };

export type QueueItem = {
  id: number;
  rule_id: string;
  issue_type: string;
  bucket: string;
  severity: string;
  title: string;
  plain_reason: string;
  amount_at_stake: number;
  priority_score: number;
  confidence: number;
  deadline: string | null;
  days_left: number | null;
  recommended_action: string;
  entity: Entity;
  evidence: Evidence[];
  status: string;
  explanation: string | null;
  draft: Draft | string | null;
};

export type Liability = {
  output_tax: number;
  itc_claim_now: number;
  itc_if_all_recovered: number;
  net_payable_now: number;
  net_payable_if_recovered: number;
  cash_impact_of_issues: number;
};

export type Summary = {
  safe_to_claim: number;
  at_risk: number;
  needs_fix: number;
  status_breakdown: Record<string, number>;
  liability: Liability;
  top5_queue: QueueItem[];
};

export type Health = { status: string; as_of_date: string; period: string; llm_provider: string };

export type EvalMetrics = Record<string, { precision: number; recall: number }>;
