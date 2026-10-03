from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

class IssueType(str, Enum):
    MISSING_IN_GSTR2B = "MISSING_IN_GSTR2B"
    SUPPLIER_GSTIN_CANCELLED = "SUPPLIER_GSTIN_CANCELLED"
    PAYMENT_180_DAY_RISK = "PAYMENT_180_DAY_RISK"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    WRONG_TAX_RATE = "WRONG_TAX_RATE"
    WRONG_TAX_TYPE = "WRONG_TAX_TYPE"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    MISSING_IN_BOOKS = "MISSING_IN_BOOKS"
    SPLIT_INVOICE = "SPLIT_INVOICE"
    CIRCULAR_TRADING = "CIRCULAR_TRADING"
    STATISTICAL_ANOMALY = "STATISTICAL_ANOMALY"
    UNMATCHED_PAYMENT = "UNMATCHED_PAYMENT"
    UNMATCHED_RECEIPT = "UNMATCHED_RECEIPT"
    UPI_SHORT_SETTLEMENT_UNEXPLAINED = "UPI_SHORT_SETTLEMENT_UNEXPLAINED"
    PERIOD_CUTOFF = "PERIOD_CUTOFF"
    ROUNDING_DIFF = "ROUNDING_DIFF"
    UPI_MDR_ADJUSTED = "UPI_MDR_ADJUSTED"

class Bucket(str, Enum):
    AT_RISK = "AT_RISK"
    NEEDS_FIX = "NEEDS_FIX"
    REVIEW = "REVIEW"
    AUTO_RESOLVED = "AUTO_RESOLVED"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Action(str, Enum):
    CHASE_SUPPLIER = "CHASE_SUPPLIER"
    HOLD_PAYMENT = "HOLD_PAYMENT"
    PAY_NOW = "PAY_NOW"
    REVERSE_ITC = "REVERSE_ITC"
    ASK_CREDIT_NOTE = "ASK_CREDIT_NOTE"
    CORRECT_BOOKS = "CORRECT_BOOKS"
    REMOVE_DUPLICATE = "REMOVE_DUPLICATE"
    RECORD_INVOICE = "RECORD_INVOICE"
    INVESTIGATE = "INVESTIGATE"
    NO_ACTION = "NO_ACTION"

class RecordStatus(str, Enum):
    MATCHED = "MATCHED"
    MATCHED_ADJUSTED = "MATCHED_ADJUSTED"
    DISCREPANT = "DISCREPANT"
    UNMATCHED = "UNMATCHED"
    DUPLICATE = "DUPLICATE"

class QueueStatus(str, Enum):
    OPEN = "OPEN"
    ACTIONED = "ACTIONED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class HealthResponse(BaseModel):
    status: str
    as_of_date: str
    period: str
    llm_provider: str

class EntityInfo(BaseModel):
    type: str
    id: int
    invoice_no: Optional[str] = None
    invoice_date: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None

class EvidenceItem(BaseModel):
    label: str
    value: str
    source: str

class QueueItem(BaseModel):
    id: int
    rule_id: str
    issue_type: IssueType
    bucket: Bucket
    severity: Severity
    title: str
    plain_reason: str
    amount_at_stake: float
    priority_score: float
    confidence: float
    deadline: Optional[str] = None
    days_left: Optional[int] = None
    recommended_action: Action
    entity: EntityInfo
    evidence: List[EvidenceItem]
    status: QueueStatus
    explanation: Optional[str] = None
    draft: Optional[str] = None

class QueueDetail(QueueItem):
    pass

class LiabilityResponse(BaseModel):
    output_tax: float
    itc_claim_now: float
    itc_if_all_recovered: float
    net_payable_now: float
    net_payable_if_recovered: float
    cash_impact_of_issues: float

class StatusBreakdown(BaseModel):
    matched: int
    matched_adjusted: int
    discrepant: int
    unmatched: int
    duplicate: int

class SummaryResponse(BaseModel):
    safe_to_claim: float
    at_risk: float
    needs_fix: float
    status_breakdown: StatusBreakdown
    liability: LiabilityResponse
    top5_queue: List[QueueItem]

class ReconStatusResponse(BaseModel):
    purchase_books: StatusBreakdown
    supplier_invoices: StatusBreakdown
    gstr2b_entries: StatusBreakdown
    sales_invoices: StatusBreakdown
    bank_transactions: StatusBreakdown

class RecordItem(BaseModel):
    id: int
    source: str
    status: RecordStatus
    data: Dict[str, Any]

class RecordsPage(BaseModel):
    items: List[RecordItem]
    total: int
    page: int
    page_size: int

class SupplierSummary(BaseModel):
    id: int
    name: str
    gstin: str
    score: float

class SupplierDetail(SupplierSummary):
    factors: Dict[str, Any]
    issues: List[QueueItem]

class GraphNode(BaseModel):
    id: str
    name: str
    is_supplier: bool
    val: float

class GraphEdge(BaseModel):
    source: str
    target: str
    val: float

class GraphCycle(BaseModel):
    nodes: List[str]
    value: float

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    cycles: List[GraphCycle]

class AuditRow(BaseModel):
    id: int
    ts: str
    actor: str
    action: str
    entity_type: str
    entity_id: int
    payload_json: str
    hash: str

class AuditVerify(BaseModel):
    valid: bool
    broken_at_id: Optional[int] = None

class EvalMetric(BaseModel):
    precision: float
    recall: float

class EvaluationResponse(BaseModel):
    metrics: Dict[str, EvalMetric]

class RulesResponse(BaseModel):
    active_config: Dict[str, Any]
    rate_table: List[Dict[str, Any]]

class RunSummary(BaseModel):
    run_id: int
    started_at: str
    duration_ms: int
    period: str
    counts: Dict[str, int]
