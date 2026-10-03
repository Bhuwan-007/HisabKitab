import pytest
import pandas as pd
from app.rules import upi_mdr
from app.matching.invoice_match import MatchRecord
from app.config import config

class DummyDataset:
    pass

def test_mdr_fee_calculation():
    # exactly 2000 has no fee
    assert upi_mdr.get_mdr_fee({"channel": "UPI", "txn_kind": "P2M", "txn_date": "2026-10-15"}, 2000, config) == 0.0
    # 2001 has fee
    assert upi_mdr.get_mdr_fee({"channel": "UPI", "txn_kind": "P2M", "txn_date": "2026-10-15"}, 2001, config) > 0.0
    # 75000 and above is capped at 300 (75000 * 0.004 = 300.0)
    assert upi_mdr.get_mdr_fee({"channel": "UPI", "txn_kind": "P2M", "txn_date": "2026-10-15"}, 80000, config) == 300.0
    # 3000 gives 12
    assert upi_mdr.get_mdr_fee({"channel": "UPI", "txn_kind": "P2M", "txn_date": "2026-10-15"}, 3000, config) == 12.0
    # exempt merchant flag turns fee off
    cfg_exempt = config.model_copy()
    cfg_exempt.UPI_MDR_EXEMPT_MERCHANT = True
    assert upi_mdr.get_mdr_fee({"channel": "UPI", "txn_kind": "P2M", "txn_date": "2026-10-15"}, 3000, cfg_exempt) == 0.0

def test_upi_mdr_adjusted_and_short():
    ds = DummyDataset()
    ds.bank = pd.DataFrame([
        {"id": 1, "amount": 2988, "txn_date": "2026-10-15", "channel": "UPI", "txn_kind": "P2M"},
        {"id": 2, "amount": 2900, "txn_date": "2026-10-15", "channel": "UPI", "txn_kind": "P2M"}
    ])
    ds.sales = pd.DataFrame([
        {"id": 10, "total": 3000},
        {"id": 20, "total": 3000}
    ])
    
    matches = [
        MatchRecord('bank_transaction', 1, 'sales_invoice', 10, 'MDR_ADJUSTED', 1.0, {"mdr_fee": 12.0}),
        MatchRecord('bank_transaction', 2, 'sales_invoice', 20, 'UPI_UNEXPLAINED_SHORT', 0.9, {"amount_diff": 100.0})
    ]
    
    findings = upi_mdr.run(ds, matches, config)
    
    f_mdr = [f for f in findings if f.issue_type == 'UPI_MDR_ADJUSTED']
    assert len(f_mdr) == 1
    assert f_mdr[0].entity_id == 1
    
    f_short = [f for f in findings if f.issue_type == 'UPI_SHORT_SETTLEMENT_UNEXPLAINED']
    assert len(f_short) == 1
    assert f_short[0].entity_id == 2
    assert f_short[0].amount_at_stake == 100.0
