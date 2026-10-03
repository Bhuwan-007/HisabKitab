import pytest
import pandas as pd
from datetime import date
from app.rules import payment_clock
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_payment_clock_180_days():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # Decoy: fully paid, 181 days old
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-04-18", "total": 1000, "cgst": 90, "sgst": 90, "igst": 0},
        # PAY_NOW: unpaid, 180 days exactly (AS_OF_DATE = 2026-10-18 - 180 = 2026-04-21 ... wait, 2026-04-21 + 180 = 2026-10-18)
        {"id": 2, "supplier_id": 10, "invoice_date": "2026-04-21", "total": 1000, "cgst": 90, "sgst": 90, "igst": 0},
        # REVERSE_ITC: unpaid, 181 days old
        {"id": 3, "supplier_id": 10, "invoice_date": "2026-04-20", "total": 1000, "cgst": 90, "sgst": 90, "igst": 0},
        # Batch payment: partially paid?
        {"id": 4, "supplier_id": 10, "invoice_date": "2026-04-20", "total": 1000, "cgst": 90, "sgst": 90, "igst": 0},
        {"id": 5, "supplier_id": 10, "invoice_date": "2026-04-20", "total": 1000, "cgst": 90, "sgst": 90, "igst": 0},
    ])
    ds.bank = pd.DataFrame([
        {"id": 100, "amount": 1000, "direction": "DEBIT"},
        {"id": 101, "amount": 2000, "direction": "DEBIT"}
    ])
    
    matches = [
        MatchRecord('bank_transaction', 100, 'purchase_books', 1, 'PAYMENT_EXACT', 1.0, {}),
        MatchRecord('bank_transaction', 101, 'purchase_books', 4, 'BATCH_PAYMENT', 0.9, {}),
        MatchRecord('bank_transaction', 101, 'purchase_books', 5, 'BATCH_PAYMENT', 0.9, {})
    ]
    
    findings = payment_clock.run(ds, matches, config)
    f_risk = [f for f in findings if f.issue_type == 'PAYMENT_180_DAY_RISK']
    
    assert len(f_risk) == 2
    
    f2 = next(f for f in f_risk if f.entity_id == 2)
    assert f2.action == 'PAY_NOW'
    assert f2.amount_at_stake == 180.0
    
    f3 = next(f for f in f_risk if f.entity_id == 3)
    assert f3.action == 'REVERSE_ITC'
