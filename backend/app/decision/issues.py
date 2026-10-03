import json
import pandas as pd
from app.models import Issue
from app.decision.priority import calculate_priority_severity
from app.llm.templates import get_fallback_explanation
from datetime import datetime
from app.config import config

def build_issues(findings, supplier_scores, run_id: int):
    issues = []
    
    as_of = pd.to_datetime(config.AS_OF_DATE).date()
    
    for f in findings:
        days_left = None
        if f.deadline:
            days_left = (f.deadline - as_of).days
            
        prio_info = calculate_priority_severity(f.issue_type, f.amount_at_stake, f.confidence, days_left)
        
        # Serialize evidence
        evidence_dicts = [{"label": e.label, "value": str(e.value), "source": e.source} for e in f.evidence]
        
        plain_reason = get_fallback_explanation(f)
        
        issue = Issue(
            run_id=run_id,
            rule_id=f.rule_id,
            issue_type=f.issue_type,
            bucket=prio_info['bucket'],
            severity=prio_info['severity'],
            title=f.reason or f.issue_type,
            plain_reason=plain_reason,
            amount_at_stake=f.amount_at_stake,
            priority_score=prio_info['priority_score'],
            deadline=f.deadline,
            days_left=days_left,
            recommended_action=f.action,
            entity_type=f.entity_type,
            entity_id=int(f.entity_id) if pd.notna(f.entity_id) else None,
            supplier_id=int(f.supplier_id) if pd.notna(f.supplier_id) else None,
            confidence=f.confidence,
            evidence_json=json.dumps(evidence_dicts),
            status='OPEN',
            explanation=None,
            draft_subject=None,
            draft_body=None
        )
        issues.append(issue)
        
    return issues
