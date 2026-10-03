from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any, List
from datetime import date
from sqlalchemy import Column, JSON

class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gstin: str
    state_code: str

class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    gstin: str
    name: str
    state_code: str
    gstin_status: str
    status_changed_on: Optional[date] = None
    avg_filing_delay_days: int
    filings_last_6m_on_time: int
    is_shell_flag: bool

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gstin: Optional[str] = None
    state_code: str

class PurchaseBook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_id: int
    invoice_no_raw: str
    invoice_no_norm: str
    invoice_date: date
    booked_on: date
    itc_period: str
    hsn: str
    taxable_value: float
    rate_pct: float
    cgst: float
    sgst: float
    igst: float
    total: float
    place_of_supply_state: str

class SupplierInvoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_gstin: str
    invoice_no_raw: str
    invoice_no_norm: str
    invoice_date: date
    hsn: str
    taxable_value: float
    rate_pct: float
    cgst: float
    sgst: float
    igst: float
    total: float
    source_file: Optional[str] = None

class GSTR2BEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier_gstin: str
    invoice_no_raw: str
    invoice_no_norm: str
    invoice_date: date
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    return_period: str
    filed_on: date

class SalesInvoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int
    invoice_no: str
    invoice_date: date
    hsn: str
    taxable_value: float
    rate_pct: float
    cgst: float
    sgst: float
    igst: float
    total: float

class BankTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    txn_date: date
    direction: str
    amount: float
    channel: str
    narration: str
    counterparty_hint: str
    reference: str
    txn_kind: Optional[str] = None

class TradeLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_gstin: str
    to_gstin: str
    value: float
    invoice_count: int
    period: str

class RateTable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hsn_prefix: str
    description: str
    rate_before: float
    rate_after: float
    effective_from: Optional[date] = None

class ReconRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: str
    duration_ms: int
    period: str
    counts_json: str

class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int
    left_type: str
    left_id: int
    right_type: str
    right_id: int
    match_type: str
    confidence: float
    diffs_json: str

class RecordStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int
    record_type: str
    record_id: int
    status: str

class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int
    rule_id: str
    issue_type: str
    bucket: str
    severity: str
    title: str
    plain_reason: str
    amount_at_stake: float
    priority_score: float
    deadline: Optional[date] = None
    days_left: Optional[int] = None
    recommended_action: str
    entity_type: str
    entity_id: int
    supplier_id: Optional[int] = None
    confidence: float
    evidence_json: str
    status: str
    explanation: Optional[str] = None
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None

class SupplierScore(SQLModel, table=True):
    supplier_id: int = Field(primary_key=True)
    run_id: int = Field(primary_key=True)
    score: float
    factors_json: str

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: str
    actor: str
    action: str
    entity_type: str
    entity_id: int
    payload_json: str
    prev_hash: str
    hash: str

class LlmCache(SQLModel, table=True):
    key: str = Field(primary_key=True)
    response: str
    created_at: str

class GroundTruth(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str
    entity_id: int
    injected_issue_type: Optional[str] = None
    note: str
