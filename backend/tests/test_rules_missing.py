import pytest
import pandas as pd
from datetime import date
from app.rules import missing
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_missing_in_gstr2b():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-09-15", "cgst": 9, "sgst": 9, "igst": 0},
        {"id": 2, "supplier_id": 10, "invoice_date": "2026-09-16", "cgst": 9, "sgst": 9, "igst": 0}
    ])
    ds.gstr2b = pd.DataFrame(columns=['id', 'supplier_gstin', 'cgst', 'sgst', 'igst'])
    ds.suppliers = pd.DataFrame([{"id": 10, "gstin": "A", "gstin_status": "ACTIVE", "status_changed_on": None}])
    
    # id 1 is matched
    matches = [MatchRecord('purchase_books', 1, 'gstr2b', 100, 'EXACT', 1.0, {})]
    
    findings = missing.run(ds, matches, config)
    f_missing = [f for f in findings if f.issue_type == "MISSING_IN_GSTR2B"]
    
    assert len(f_missing) == 1
    assert f_missing[0].entity_id == 2
    assert f_missing[0].deadline == date(2026, 10, config.GSTR1_DUE_DAY_OF_MONTH)

def test_missing_in_books():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame(columns=['id', 'supplier_id', 'invoice_date', 'cgst', 'sgst', 'igst'])
    ds.gstr2b = pd.DataFrame([
        {"id": 100, "supplier_gstin": "A", "cgst": 9, "sgst": 9, "igst": 0},
        {"id": 101, "supplier_gstin": "A", "cgst": 9, "sgst": 9, "igst": 0}
    ])
    ds.suppliers = pd.DataFrame([{"id": 10, "gstin": "A", "gstin_status": "ACTIVE", "status_changed_on": None}])
    
    # 100 is matched
    matches = [MatchRecord('purchase_books', 1, 'gstr2b', 100, 'EXACT', 1.0, {})]
    
    findings = missing.run(ds, matches, config)
    f_missing = [f for f in findings if f.issue_type == "MISSING_IN_BOOKS"]
    
    assert len(f_missing) == 1
    assert f_missing[0].entity_id == 101
    assert f_missing[0].supplier_id == 10
    
def test_cancelled_supplier():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # decoy: before cancellation
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0},
        # positive: on or after cancellation
        {"id": 2, "supplier_id": 10, "invoice_date": "2026-01-02", "cgst": 9, "sgst": 9, "igst": 0}
    ])
    ds.gstr2b = pd.DataFrame(columns=['id', 'supplier_gstin', 'cgst', 'sgst', 'igst'])
    ds.suppliers = pd.DataFrame([{"id": 10, "gstin": "A", "gstin_status": "CANCELLED", "status_changed_on": "2026-01-02"}])
    
    matches = []
    
    findings = missing.run(ds, matches, config)
    f_canc = [f for f in findings if f.issue_type == "SUPPLIER_GSTIN_CANCELLED"]
    
    assert len(f_canc) == 1
    assert f_canc[0].entity_id == 2
