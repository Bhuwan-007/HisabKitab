import json
import pandas as pd
from app.models import Issue
from app.decision.priority import calculate_priority_severity
from app.llm.templates import get_fallback_explanation
from datetime import datetime
from app.config import config

def build_issues(findings, supplier_scores, run_id: int, ds):
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
        
        ent_id = int(f.entity_id) if pd.notna(f.entity_id) else None
        sup_id = int(f.supplier_id) if pd.notna(f.supplier_id) else None
        
        # Find entity details
        inv_no = None
        inv_dt = None
        sup_name = None
        
        if sup_id is not None and not ds.suppliers.empty:
            sup_row = ds.suppliers[ds.suppliers['id'] == sup_id]
            if not sup_row.empty:
                sup_name = sup_row.iloc[0]['name']
                
        if ent_id is not None:
            df = None
            if f.entity_type == 'purchase_invoice':
                df = ds.purchase_books
            elif f.entity_type == 'gstr2b':
                df = ds.gstr2b
            elif f.entity_type == 'sales_invoice':
                df = ds.sales
            elif f.entity_type == 'bank_transaction':
                df = ds.bank
                
            if df is not None and not df.empty and 'id' in df.columns:
                row = df[df['id'] == ent_id]
                if not row.empty:
                    row = row.iloc[0]
                    if 'invoice_no_raw' in row:
                        inv_no = row['invoice_no_raw']
                    elif 'invoice_no' in row:
                        inv_no = row['invoice_no']
                    if 'invoice_date' in row and pd.notna(row['invoice_date']):
                        try:
                            # Might be string or datetime
                            if isinstance(row['invoice_date'], str):
                                inv_dt = row['invoice_date']
                            else:
                                inv_dt = row['invoice_date'].strftime('%Y-%m-%d')
                        except:
                            pass
        
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
            entity_id=ent_id,
            supplier_id=sup_id,
            confidence=f.confidence,
            evidence_json=json.dumps(evidence_dicts),
            status='OPEN',
            explanation=None,
            draft_subject=None,
            draft_body=None
        )
        
        issue._inv_no = inv_no
        issue._inv_dt = inv_dt
        issue._sup_name = sup_name
        issues.append(issue)
        
    return issues
