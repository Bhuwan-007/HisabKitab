from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import date

@dataclass
class Evidence:
    label: str
    value: Any
    source: str

@dataclass
class Finding:
    rule_id: str
    issue_type: str
    entity_type: str
    entity_id: int
    supplier_id: Optional[int]
    amount_at_stake: float
    confidence: float
    evidence: List[Evidence]
    deadline: Optional[date]
    action: str
    bucket: str
    reason: str = ""
