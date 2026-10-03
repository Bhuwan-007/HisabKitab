import pytest
import pandas as pd
from app.rules import duplicates
from app.config import config

class DummyDataset:
    pass

def test_duplicates():
    ds = DummyDataset()
    ds.suppliers = pd.DataFrame([{"id": 1}])
    ds.purchase_books = pd.DataFrame([
        # Exact dupes
        {"id": 1, "supplier_id": 1, "invoice_no_norm": "123", "invoice_no_raw": "123", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        {"id": 2, "supplier_id": 1, "invoice_no_norm": "123", "invoice_no_raw": "123", "invoice_date": "2026-01-02", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        
        # Fuzzy dupes
        {"id": 3, "supplier_id": 1, "invoice_no_norm": "456", "invoice_no_raw": "INV456", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        {"id": 4, "supplier_id": 1, "invoice_no_norm": "456A", "invoice_no_raw": "INV456A", "invoice_date": "2026-01-02", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100},
        
        # Decoys
        {"id": 5, "supplier_id": 1, "invoice_no_norm": "999", "invoice_no_raw": "INV999", "invoice_date": "2026-01-01", "cgst": 9, "sgst": 9, "igst": 0, "taxable_value": 100}
    ])
    
    findings = duplicates.run(ds, [], config)
    f_dup = [f for f in findings if f.issue_type == "DUPLICATE_INVOICE"]
    
    assert len(f_dup) == 2
    
    exact = next(f for f in f_dup if f.entity_id == 2)
    assert exact.confidence == 1.0
    
    fuzzy = next(f for f in f_dup if f.entity_id == 4)
    assert fuzzy.confidence == 0.85
