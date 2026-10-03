import pytest
import pandas as pd
from app.rules import cutoff
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_cutoff():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # Decoy: not last 3 days
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-01-15", "itc_period": "2026-02"},
        # Positive: last 3 days, next month itc_period
        {"id": 2, "supplier_id": 10, "invoice_date": "2026-01-30", "itc_period": "2026-02"},
    ])
    ds.gstr2b = pd.DataFrame(columns=['id', 'supplier_gstin', 'cgst', 'sgst', 'igst', 'return_period'])
    ds.bank = pd.DataFrame(columns=['id', 'txn_date'])
    
    findings = cutoff.run(ds, [], config)
    f_cut = [f for f in findings if f.issue_type == "PERIOD_CUTOFF"]
    
    assert len(f_cut) == 1
    assert f_cut[0].entity_id == 2
    assert f_cut[0].action == "INVESTIGATE"

def test_rounding():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0}
    ])
    ds.gstr2b = pd.DataFrame([
        {"id": 10, "cgst": 9.5, "sgst": 9.4, "igst": 0} # sum 18.9 vs 18.0 -> diff 0.9
    ])
    ds.bank = pd.DataFrame(columns=['id', 'txn_date'])
    
    matches = [MatchRecord('purchase_books', 1, 'gstr2b', 10, 'EXACT', 1.0, {})]
    
    findings = cutoff.run(ds, matches, config)
    f_rnd = [f for f in findings if f.issue_type == "ROUNDING_DIFF"]
    
    assert len(f_rnd) == 1
    assert f_rnd[0].entity_id == 1
    assert f_rnd[0].bucket == "AUTO_RESOLVED"
