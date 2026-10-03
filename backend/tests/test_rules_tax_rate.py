import pytest
import pandas as pd
from datetime import date
from app.rules import tax_rate
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_tax_amount_mismatch():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # overcharge
        {"id": 1, "supplier_id": 10, "cgst": 10, "sgst": 10, "igst": 0, "invoice_date": "2026-01-01", "hsn": "1234", "rate_pct": 18},
        # undercharge
        {"id": 2, "supplier_id": 10, "cgst": 8, "sgst": 8, "igst": 0, "invoice_date": "2026-01-01", "hsn": "1234", "rate_pct": 18}
    ])
    ds.gstr2b = pd.DataFrame([
        {"id": 101, "cgst": 9, "sgst": 9, "igst": 0},
        {"id": 102, "cgst": 9, "sgst": 9, "igst": 0}
    ])
    ds.supplier_invoices = pd.DataFrame(columns=['id', 'rate_pct'])
    ds.rates = pd.DataFrame([
        {"hsn_prefix": "1234", "rate_before": 18, "rate_after": 18}
    ])
    
    matches = [
        MatchRecord('purchase_books', 1, 'gstr2b', 101, 'EXACT', 1.0, {}),
        MatchRecord('purchase_books', 2, 'gstr2b', 102, 'EXACT', 1.0, {})
    ]
    
    findings = tax_rate.run(ds, matches, config)
    f_amt = [f for f in findings if f.issue_type == "AMOUNT_MISMATCH"]
    
    assert len(f_amt) == 2
    
    f1 = next(f for f in f_amt if f.entity_id == 1)
    assert f1.amount_at_stake == 2.0
    assert f1.action == "ASK_CREDIT_NOTE"
    
    f2 = next(f for f in f_amt if f.entity_id == 2)
    assert f2.amount_at_stake == 0.0
    assert f2.action == "CORRECT_BOOKS"

def test_wrong_tax_rate():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # Decoy: Before cutover, old rate (28) -> correct
        {"id": 1, "supplier_id": 10, "invoice_date": "2025-09-20", "hsn": "9999", "rate_pct": 28, "taxable_value": 100},
        # Positive (overcharge): After cutover, old rate (28) -> wrong
        {"id": 2, "supplier_id": 10, "invoice_date": "2025-09-23", "hsn": "9999", "rate_pct": 28, "taxable_value": 100},
        # Positive (undercharge): After cutover, lower than new rate (12 instead of 18)
        {"id": 3, "supplier_id": 10, "invoice_date": "2025-09-23", "hsn": "9999", "rate_pct": 12, "taxable_value": 100}
    ])
    ds.gstr2b = pd.DataFrame(columns=['id', 'supplier_gstin', 'cgst', 'sgst', 'igst', 'return_period'])
    ds.supplier_invoices = pd.DataFrame(columns=['id', 'rate_pct'])
    ds.rates = pd.DataFrame([
        {"hsn_prefix": "9999", "rate_before": 28, "rate_after": 18}
    ])
    
    findings = tax_rate.run(ds, [], config)
    f_rate = [f for f in findings if f.issue_type == "WRONG_TAX_RATE"]
    
    # 1 should be missing (decoy)
    assert len(f_rate) == 2
    
    f2 = next(f for f in f_rate if f.entity_id == 2)
    assert f2.bucket == "NEEDS_FIX"
    assert f2.amount_at_stake == 10.0 # 28 - 18
    assert "old rate used" in f2.reason
    
    f3 = next(f for f in f_rate if f.entity_id == 3)
    assert f3.bucket == "REVIEW"
    assert f3.amount_at_stake == 0.0
