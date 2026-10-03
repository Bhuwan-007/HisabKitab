import pytest
import pandas as pd
from app.matching.invoice_match import match_invoices_pair, MatchRecord
from app.matching.payment_match import match_payments
from app.config import config

def test_exact_and_cross_supplier():
    left = pd.DataFrame([
        {"id": 1, "supplier_gstin": "A", "invoice_no_norm": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        {"id": 2, "supplier_gstin": "B", "invoice_no_norm": "456", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100}
    ])
    right = pd.DataFrame([
        {"id": 10, "supplier_gstin": "A", "invoice_no_norm": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        {"id": 20, "supplier_gstin": "C", "invoice_no_norm": "456", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100}
    ])
    matches = match_invoices_pair(left, right, "left", "right")
    assert len(matches) == 1
    assert matches[0].left_id == 1
    assert matches[0].right_id == 10
    assert matches[0].match_type == "EXACT"

def test_fuzzy_match():
    left = pd.DataFrame([
        {"id": 1, "supplier_gstin": "A", "invoice_no_norm": "INV45A", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    right = pd.DataFrame([
        {"id": 10, "supplier_gstin": "A", "invoice_no_norm": "INV45", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    matches = match_invoices_pair(left, right, "left", "right")
    assert len(matches) == 1
    assert matches[0].match_type == "FUZZY"

def test_amount_match():
    left = pd.DataFrame([
        {"id": 1, "supplier_gstin": "A", "invoice_no_norm": "COMPLETELY", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    right = pd.DataFrame([
        {"id": 10, "supplier_gstin": "A", "invoice_no_norm": "DIFFERENT", "invoice_date": "2026-01-05", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    matches = match_invoices_pair(left, right, "left", "right")
    assert len(matches) == 1
    assert matches[0].match_type == "AMOUNT"
    assert matches[0].confidence == 0.55

def test_never_matched_twice_duplicate():
    left = pd.DataFrame([
        {"id": 1, "supplier_gstin": "A", "invoice_no_norm": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        {"id": 2, "supplier_gstin": "A", "invoice_no_norm": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    right = pd.DataFrame([
        {"id": 10, "supplier_gstin": "A", "invoice_no_norm": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
    ])
    matches = match_invoices_pair(left, right, "left", "right")
    assert len(matches) == 1
    assert matches[0].left_id in [1, 2]
    assert matches[0].right_id == 10

class DummyDataset:
    pass

def test_batch_payment():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        {"id": 1, "supplier_id": 100, "invoice_no_raw": "A", "invoice_date": "2026-01-01", "total": 100},
        {"id": 2, "supplier_id": 100, "invoice_no_raw": "B", "invoice_date": "2026-01-05", "total": 200},
    ])
    ds.suppliers = pd.DataFrame([
        {"id": 100, "name": "Acme"}
    ])
    ds.bank = pd.DataFrame([
        {"id": 10, "direction": "DEBIT", "amount": 300, "counterparty_hint": "Acme", "reference": "", "narration": ""}
    ])
    ds.sales = pd.DataFrame(columns=["id", "total"])
    
    matches = match_payments(ds)
    assert len(matches) == 2
    assert matches[0].match_type == "BATCH_PAYMENT"
    assert matches[1].match_type == "BATCH_PAYMENT"
