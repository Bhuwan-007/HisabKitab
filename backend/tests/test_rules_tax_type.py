import pytest
import pandas as pd
from app.rules import tax_type
from app.config import config

class DummyDataset:
    pass

def test_tax_type():
    ds = DummyDataset()
    ds.business = pd.DataFrame([{"state_code": "07"}])
    ds.suppliers = pd.DataFrame([
        {"id": 1, "state_code": "07"}, # intra
        {"id": 2, "state_code": "27"}  # inter
    ])
    
    ds.purchase_books = pd.DataFrame([
        # decoy 1: intra, correct
        {"id": 10, "supplier_id": 1, "cgst": 9, "sgst": 9, "igst": 0},
        # decoy 2: inter, correct
        {"id": 11, "supplier_id": 2, "cgst": 0, "sgst": 0, "igst": 18},
        # wrong: intra, charged igst
        {"id": 12, "supplier_id": 1, "cgst": 0, "sgst": 0, "igst": 18},
        # wrong: inter, charged cgst/sgst
        {"id": 13, "supplier_id": 2, "cgst": 9, "sgst": 9, "igst": 0}
    ])
    
    findings = tax_type.run(ds, [], config)
    f_type = [f for f in findings if f.issue_type == "WRONG_TAX_TYPE"]
    
    assert len(f_type) == 2
    assert {f.entity_id for f in f_type} == {12, 13}
    for f in f_type:
        assert f.amount_at_stake == 18.0
