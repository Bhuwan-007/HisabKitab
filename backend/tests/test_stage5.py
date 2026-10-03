import pytest
import json
from sqlmodel import Session, select, create_engine
from app.models import SQLModel, Issue, GroundTruth, AuditLog
from app.decision.priority import calculate_priority_severity, get_bucket
from app.decision.liability import compute_liability
from app.pipeline import run_reconciliation
from app.audit.chain import append_audit, verify_chain
from app.schemas import QueueStatus
from fastapi.testclient import TestClient
from app.main import app
from app.config import config
from app.ingest.loaders import load_all

from app.db import engine as db_engine

client = TestClient(app)

@pytest.fixture
def engine():
    return db_engine

def test_priority_and_severity():
    # priority_score = amount_at_stake * urgency_multiplier * confidence
    
    # 1. 100k, low confidence 0.5, no deadline -> 50k HIGH
    p = calculate_priority_severity('MISSING_IN_GSTR2B', 100000, 0.5, None)
    assert p['priority_score'] == 50000
    assert p['severity'] == 'HIGH'
    
    # 2. urgency multiplier: days_left <= 7 -> 1.5, <=15 -> 1.25
    p2 = calculate_priority_severity('PAYMENT_180_DAY_RISK', 10000, 1.0, 5) # 1.5 * 10k = 15k
    assert p2['priority_score'] == 15000
    assert p2['severity'] == 'MEDIUM'
    
    p3 = calculate_priority_severity('PAYMENT_180_DAY_RISK', 10000, 1.0, 10) # 1.25 * 10k = 12.5k
    assert p3['priority_score'] == 12500
    assert p3['severity'] == 'MEDIUM'
    
    # 3. Cancelled always CRITICAL
    p4 = calculate_priority_severity('SUPPLIER_GSTIN_CANCELLED', 0, 1.0, None)
    assert p4['severity'] == 'CRITICAL'
    
    # 4. REVIEW bucket with 0 amount -> 1000 * confidence
    p5 = calculate_priority_severity('CIRCULAR_TRADING', 0, 0.8, None)
    assert p5['priority_score'] == 800
    assert p5['bucket'] == 'REVIEW'

def test_kpi_integrity(engine):
    with Session(engine) as session:
        # Assuming seed is already run via the script
        ds = load_all()
        # Find the run
        run_res = run_reconciliation(session, config.OPEN_PERIOD)
        run_id = run_res['run_id']
        issues = session.exec(select(Issue).where(Issue.run_id == run_id)).all()
        
        liab = compute_liability(ds, issues, config.OPEN_PERIOD)
        
        # safe_to_claim + at_risk + needs_fix == total_itc_booked (when no clamping)
        assert abs(liab["safe_to_claim"] + liab["at_risk"] + liab["needs_fix"] - liab["total_itc_booked"]) < 1.0
        
def test_invoice_two_issues_counted_once(engine):
    with Session(engine) as session:
        # Create a mock scenario
        # 1 AT_RISK and 1 NEEDS_FIX on the same invoice (id 999)
        issues = [
            Issue(id=1, run_id=1, bucket='AT_RISK', entity_type='purchase_invoice', entity_id=999, amount_at_stake=1000, issue_type='A', rule_id='R1', severity='L', title='T', confidence=1.0, evidence_json='[]', status='OPEN'),
            Issue(id=2, run_id=1, bucket='NEEDS_FIX', entity_type='purchase_invoice', entity_id=999, amount_at_stake=800, issue_type='B', rule_id='R2', severity='L', title='T', confidence=1.0, evidence_json='[]', status='OPEN'),
            Issue(id=3, run_id=1, bucket='NEEDS_FIX', entity_type='purchase_invoice', entity_id=998, amount_at_stake=500, issue_type='C', rule_id='R3', severity='L', title='T', confidence=1.0, evidence_json='[]', status='OPEN'),
        ]
        
        ds = load_all() # real ds has some total_itc_booked, we don't care about it, just the logic
        liab = compute_liability(ds, issues, config.OPEN_PERIOD)
        
        # at_risk should be 1000. needs_fix should be 500 (since 999 is already in at_risk)
        assert liab["at_risk"] == 1000
        assert liab["needs_fix"] == 500

def test_queue_sorting_and_api(engine):
    resp = client.get("/api/queue")
    assert resp.status_code == 200
    queue = resp.json()
    
    # Check descending priority
    scores = [q['priority_score'] for q in queue]
    assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    
    # Grab one
    if queue:
        qid = queue[0]['id']
        patch_res = client.patch(f"/api/queue/{qid}", json={"status": "ACTIONED"})
        assert patch_res.status_code == 200
        assert patch_res.json()['status'] == 'ACTIONED'
        
        # Check audit
        with Session(engine) as session:
            logs = session.exec(select(AuditLog).order_by(AuditLog.id.desc())).all()
            assert logs[0].action == 'STATUS_CHANGED'
            assert str(logs[0].entity_id) == str(qid)
            
            # Verify chain
            ver = verify_chain(session)
            assert ver['valid'] == True
            
            # Tamper
            logs[0].payload_json = '{"tampered": true}'
            session.add(logs[0])
            session.commit()
            
            ver_tampered = verify_chain(session)
            assert ver_tampered['valid'] == False
            assert ver_tampered['broken_at_id'] == logs[0].id

def test_pipeline_idempotent(engine):
    with Session(engine) as session:
        res1 = run_reconciliation(session, config.OPEN_PERIOD)
        res2 = run_reconciliation(session, config.OPEN_PERIOD)
        
        assert res1['counts'] == res2['counts']

def test_evaluation(engine):
    with Session(engine) as session:
        run_reconciliation(session, config.OPEN_PERIOD)
    
    resp = client.get("/api/evaluation")
    assert resp.status_code == 200
    data = resp.json()
    
    by_type = data['metrics']
    
    # rule-based types should have high precision and recall
    for t in ['AMOUNT_MISMATCH', 'MISSING_IN_GSTR2B', 'MISSING_IN_BOOKS', 'WRONG_TAX_RATE', 'PAYMENT_180_DAY_RISK', 'SPLIT_INVOICE']:
        if t in by_type:
            assert by_type[t]['recall'] >= 0.90
            assert by_type[t]['precision'] >= 0.85
