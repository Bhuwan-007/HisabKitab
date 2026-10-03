import time
import json
import collections
from sqlmodel import Session, select, delete
from app.models import ReconRun, Match as MatchModel, RecordStatus, Issue, SupplierScore
from app.ingest.loaders import load_all
from app.matching.invoice_match import match_invoices
from app.matching.payment_match import match_payments
from app.rules import run_all_tax_rules, run_all_payment_rules
from app.risk import run_risk_layer
from app.decision.issues import build_issues
from app.audit.chain import append_audit
from app.config import config

def run_reconciliation(session: Session, period: str):
    start_time = time.time()
    
    # 0. Clear previous run
    runs = session.exec(select(ReconRun).where(ReconRun.period == period)).all()
    for run in runs:
        session.exec(delete(MatchModel).where(MatchModel.run_id == run.id))
        session.exec(delete(RecordStatus).where(RecordStatus.run_id == run.id))
        session.exec(delete(Issue).where(Issue.run_id == run.id))
        session.exec(delete(SupplierScore).where(SupplierScore.run_id == run.id))
        session.delete(run)
    session.commit()
    
    run_rec = ReconRun(
        started_at=config.AS_OF_DATE,
        duration_ms=0,
        period=period,
        counts_json="{}"
    )
    session.add(run_rec)
    session.commit()
    session.refresh(run_rec)
    run_id = run_rec.id
    
    append_audit(session, "system", "RUN_STARTED", "run", run_id, {"period": period})
    
    ds = load_all()
    
    inv_matches = match_invoices(ds)
    pay_matches = match_payments(ds)
    all_matches = inv_matches + pay_matches
    
    tax_findings = run_all_tax_rules(ds, all_matches, config)
    pay_findings = run_all_payment_rules(ds, all_matches, config)
    findings = tax_findings + pay_findings
    
    risk_result = run_risk_layer(ds, findings, config)
    findings.extend(risk_result.new_findings)
    
    issues = build_issues(findings, risk_result.supplier_scores, run_id)
    
    # Deduplicate issues: only one issue per record.
    # Priority order follows ARCHITECTURE section 8 bucket logic and BUSINESS_RULES R-ITC-01:
    # MISSING_IN_GSTR2B > PAYMENT_180_DAY_RISK so that if an invoice is both missing in 2B
    # and at 180-day risk, the MISSING finding wins (it is the harder blocker).
    type_priority = {
        'SUPPLIER_GSTIN_CANCELLED': 100,
        'DUPLICATE_INVOICE': 90,
        'CIRCULAR_TRADING': 85,
        'SPLIT_INVOICE': 80,
        'STATISTICAL_ANOMALY': 75,
        'AMOUNT_MISMATCH': 70,
        'WRONG_TAX_RATE': 65,
        'WRONG_TAX_TYPE': 60,
        'MISSING_IN_GSTR2B': 58,   # AT_RISK — outranks PAYMENT_180_DAY_RISK
        'MISSING_IN_BOOKS': 57,
        'PERIOD_CUTOFF': 55,
        'PAYMENT_180_DAY_RISK': 50,
    }
    
    best_issues = {}
    for issue in issues:
        key = (issue.entity_type, issue.entity_id)
        if key not in best_issues:
            best_issues[key] = issue
        else:
            curr = best_issues[key]
            curr_tp = type_priority.get(curr.issue_type, 0)
            new_tp = type_priority.get(issue.issue_type, 0)
            if new_tp > curr_tp or (new_tp == curr_tp and issue.priority_score > curr.priority_score):
                best_issues[key] = issue
                
    issues = list(best_issues.values())
    
    for m in all_matches:
        session.add(MatchModel(
            run_id=run_id,
            left_type=m.left_type,
            left_id=m.left_id,
            right_type=m.right_type,
            right_id=m.right_id,
            match_type=m.match_type,
            confidence=m.confidence,
            diffs_json=json.dumps(m.diffs)
        ))
        
    for issue in issues:
        session.add(issue)
        
    for sup_id, data in risk_result.supplier_scores.items():
        session.add(SupplierScore(
            supplier_id=sup_id,
            run_id=run_id,
            score=data['score'],
            factors_json=json.dumps(data['factors'])
        ))
        
    record_status_map = collections.defaultdict(dict)
    
    def set_status(t, i, status):
        prio = {"DUPLICATE": 5, "DISCREPANT": 4, "MATCHED_ADJUSTED": 3, "MATCHED": 2, "UNMATCHED": 1}
        current = record_status_map[t].get(i, "UNMATCHED")
        if prio[status] > prio.get(current, 0):
            record_status_map[t][i] = status

    for m in all_matches:
        status = 'MATCHED' if m.match_type in ('EXACT', 'PAYMENT_1TO1') else 'MATCHED_ADJUSTED'
        set_status(m.left_type, m.left_id, status)
        set_status(m.right_type, m.right_id, status)
        
    for issue in issues:
        if issue.issue_type == 'DUPLICATE_INVOICE':
            set_status(issue.entity_type, issue.entity_id, 'DUPLICATE')
        elif issue.bucket in ('AT_RISK', 'NEEDS_FIX'):
            if issue.issue_type in ('MISSING_IN_GSTR2B', 'MISSING_IN_BOOKS', 'UNMATCHED_PAYMENT', 'UNMATCHED_RECEIPT'):
                set_status(issue.entity_type, issue.entity_id, 'UNMATCHED')
            else:
                set_status(issue.entity_type, issue.entity_id, 'DISCREPANT')
                
    for t, m_dict in list(record_status_map.items()):
        for i, status in m_dict.items():
            session.add(RecordStatus(run_id=run_id, record_type=t, record_id=i, status=status))
            
        for _, row in ds.purchase_books.iterrows():
            if row['id'] not in record_status_map['purchase_books']:
                session.add(RecordStatus(run_id=run_id, record_type='purchase_books', record_id=row['id'], status='UNMATCHED'))
        for _, row in ds.gstr2b.iterrows():
            if row['id'] not in record_status_map['gstr2b_entries']:
                session.add(RecordStatus(run_id=run_id, record_type='gstr2b_entries', record_id=row['id'], status='UNMATCHED'))
        for _, row in ds.sales.iterrows():
            if row['id'] not in record_status_map['sales_invoices']:
                session.add(RecordStatus(run_id=run_id, record_type='sales_invoices', record_id=row['id'], status='UNMATCHED'))
        for _, row in ds.bank.iterrows():
            if row['id'] not in record_status_map['bank_transactions']:
                session.add(RecordStatus(run_id=run_id, record_type='bank_transactions', record_id=row['id'], status='UNMATCHED'))
    
    session.commit()
    
    issue_counts = collections.Counter(i.issue_type for i in issues)
    counts = dict(issue_counts)
    
    duration = int((time.time() - start_time) * 1000)
    run_rec.duration_ms = duration
    run_rec.counts_json = json.dumps(counts)
    session.add(run_rec)
    session.commit()
    
    append_audit(session, "system", "ISSUE_CREATED", "run", run_id, counts)
    append_audit(session, "system", "RUN_COMPLETED", "run", run_id, counts)
    
    return {
        "run_id": run_id,
        "started_at": run_rec.started_at,
        "duration_ms": duration,
        "period": period,
        "counts": counts
    }
