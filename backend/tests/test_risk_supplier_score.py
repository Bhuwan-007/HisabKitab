import pytest
import pandas as pd
from app.risk.supplier_score import score_suppliers
from app.rules.base import Finding

class DummyDataset:
    pass

def test_supplier_score():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        {"id": 1, "supplier_id": 10},
        {"id": 2, "supplier_id": 10},
        {"id": 3, "supplier_id": 11}
    ])
    ds.suppliers = pd.DataFrame([
        # Cancelled
        {"id": 10, "gstin": "A", "gstin_status": "CANCELLED", "filings_last_6m_on_time": 6, "avg_filing_delay_days": 0},
        # Normal
        {"id": 11, "gstin": "B", "gstin_status": "ACTIVE", "filings_last_6m_on_time": 3, "avg_filing_delay_days": 15}
    ])
    
    findings = [
        Finding('R', 'MISSING_IN_GSTR2B', 'purchase_invoice', 3, 11, 0, 1.0, [], None, 'A', 'B', 'C')
    ]
    
    cycles = [
        {"nodes": ["B"], "total_value": 500000}
    ]
    
    scores = score_suppliers(ds, findings, cycles)
    
    assert scores[10]['score'] == 100.0
    assert scores[10]['factors'][0]['name'] == "GSTIN cancelled"
    
    # 11:
    # Missed/late: (6-3)/6 = 0.5 * 30 = 15.0
    # Missing in 2B: 1 / 1 = 1.0 * 25 = 25.0
    # Avg delay: 15 / 30 = 0.5 * 15 = 7.5
    # Mismatch: 0
    # Loop: 1 * 15 = 15.0
    # Total = 15 + 25 + 7.5 + 0 + 15 = 62.5
    
    assert scores[11]['score'] == 62.5
    
    # Check weights sum to 100
    assert sum(f['weight'] for f in scores[11]['factors']) == 100
    assert sum(f['contribution'] for f in scores[11]['factors']) == 62.5
