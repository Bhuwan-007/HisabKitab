import pytest
import pandas as pd
from app.risk.anomalies import detect_split_invoices, detect_statistical_anomalies
from app.config import config
from app.rules.base import Finding

class DummyDataset:
    pass

def test_split_invoices():
    ds = DummyDataset()
    ds.purchase_books = pd.DataFrame([
        # Group 1: Split (sum >= 50k, each < 50k, >= 35k)
        {"id": 1, "supplier_id": 10, "invoice_date": "2026-01-01", "taxable_value": 40000, "total": 40000},
        {"id": 2, "supplier_id": 10, "invoice_date": "2026-01-02", "taxable_value": 40000, "total": 40000},
        # Group 2: Too far apart
        {"id": 3, "supplier_id": 11, "invoice_date": "2026-01-01", "taxable_value": 40000, "total": 40000},
        {"id": 4, "supplier_id": 11, "invoice_date": "2026-01-05", "taxable_value": 40000, "total": 40000},
        # Group 3: Below 70% threshold
        {"id": 5, "supplier_id": 12, "invoice_date": "2026-01-01", "taxable_value": 20000, "total": 20000},
        {"id": 6, "supplier_id": 12, "invoice_date": "2026-01-02", "taxable_value": 20000, "total": 20000},
    ])
    
    findings = detect_split_invoices(ds, config)
    
    assert len(findings) == 1
    assert findings[0].entity_id == 1
    assert findings[0].supplier_id == 10

def test_statistical_anomalies():
    ds = DummyDataset()
    # Create 40 identical normal invoices and 1 huge anomaly
    normal = [{"id": i, "supplier_id": 10, "invoice_date": f"2026-01-{i%28+1:02d}", "taxable_value": 100} for i in range(1, 41)]
    anomaly = [{"id": 100, "supplier_id": 10, "invoice_date": "2026-01-01", "taxable_value": 10000000}]
    
    ds.purchase_books = pd.DataFrame(normal + anomaly)
    
    findings = detect_statistical_anomalies(ds, [], config)
    
    # Should flag 100
    assert any(f.entity_id == 100 for f in findings)
    
    # If 100 is already flagged, it shouldn't be flagged again
    existing = [Finding('R', 'OTHER', 'purchase_invoice', 100, 10, 0, 1.0, [], None, 'A', 'B', 'C')]
    findings2 = detect_statistical_anomalies(ds, existing, config)
    assert not any(f.entity_id == 100 for f in findings2)
