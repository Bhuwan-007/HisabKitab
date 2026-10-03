import pytest
import os
import json
from app.seed.generator import generate_data
from app.db import engine
from sqlmodel import Session, select
from app.models import PurchaseBook, GroundTruth, BankTransaction, Supplier

def test_generate_data():
    generate_data()
    with Session(engine) as session:
        pb_count = session.exec(select(PurchaseBook)).all()
        assert 500 <= len(pb_count) <= 550
        
        gts = session.exec(select(GroundTruth)).all()
        counts = {}
        for gt in gts:
            if gt.injected_issue_type:
                counts[gt.injected_issue_type] = counts.get(gt.injected_issue_type, 0) + 1
        
        assert counts["MISSING_IN_GSTR2B"] == 14
        assert counts["SUPPLIER_GSTIN_CANCELLED"] == 6
        assert counts["AMOUNT_MISMATCH"] == 10
        assert counts["DUPLICATE_INVOICE"] == 8
        assert counts["WRONG_TAX_RATE"] == 10
        assert counts["WRONG_TAX_TYPE"] == 4
        assert counts["ROUNDING_DIFF"] == 15
        assert counts["PERIOD_CUTOFF"] == 6
        assert counts["PAYMENT_180_DAY_RISK"] == 8
        assert counts["SPLIT_INVOICE"] == 9
        assert counts["MISSING_IN_BOOKS"] == 6
        assert counts["STATISTICAL_ANOMALY"] == 6
        assert counts["UNMATCHED_PAYMENT"] == 5
        assert counts["UPI_MDR_ADJUSTED"] == 20
        assert counts["UPI_SHORT_SETTLEMENT_UNEXPLAINED"] == 3
        assert counts["UNMATCHED_RECEIPT"] == 4
        assert counts["CIRCULAR_TRADING"] == 7
        
        # Test decoys
        decoys = [gt for gt in gts if not gt.injected_issue_type]
        assert len(decoys) == 26 # 18 invoices + 8 bank
        
        # Supplier GSTIN check
        sups = session.exec(select(Supplier)).all()
        for sup in sups:
            assert sup.gstin != "07ZZZZZ9999Z1Z1"
            
        # Invoice number variants check
        variants = sum(1 for p in pb_count if p.invoice_no_raw != f"INV/{p.id}" and not getattr(p, "is_dup", False) and not getattr(p, "is_split", False))
        # At least 15%
        assert variants / 520 > 0.15
        
        # At least one UPI receipt exactly at the 300 cap
        bt = session.exec(select(BankTransaction)).all()
        has_capped = any(b.amount == 80000.0 - 300.0 for b in bt if b.direction == "CREDIT" and b.channel == "UPI")
        assert has_capped
