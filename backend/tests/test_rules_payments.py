import pytest
import pandas as pd
from app.rules import payments
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_unmatched_payments():
    ds = DummyDataset()
    ds.bank = pd.DataFrame([
        {"id": 1, "amount": 1000, "direction": "DEBIT"},
        {"id": 2, "amount": 2000, "direction": "DEBIT"},
        {"id": 3, "amount": 3000, "direction": "CREDIT"},
        {"id": 4, "amount": 4000, "direction": "CREDIT"}
    ])
    
    matches = [
        MatchRecord('bank_transaction', 1, 'purchase_books', 10, 'PAYMENT_EXACT', 1.0, {}),
        MatchRecord('bank_transaction', 3, 'sales_invoice', 20, 'RECEIPT_EXACT', 1.0, {})
    ]
    
    findings = payments.run(ds, matches, config)
    
    up = [f for f in findings if f.issue_type == 'UNMATCHED_PAYMENT']
    assert len(up) == 1
    assert up[0].entity_id == 2
    
    ur = [f for f in findings if f.issue_type == 'UNMATCHED_RECEIPT']
    assert len(ur) == 1
    assert ur[0].entity_id == 4
