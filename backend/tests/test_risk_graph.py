import pytest
import pandas as pd
from app.risk.graph import run

class DummyDataset:
    pass

def test_graph_cycles():
    ds = DummyDataset()
    ds.suppliers = pd.DataFrame([
        {"id": 10, "gstin": "A"},
        {"id": 11, "gstin": "C"}
    ])
    ds.trade_links = pd.DataFrame([
        # Cycle 1: A -> B -> C -> A (length 3, sum = 600,000)
        {"from_gstin": "A", "to_gstin": "B", "value": 200000},
        {"from_gstin": "B", "to_gstin": "C", "value": 200000},
        {"from_gstin": "C", "to_gstin": "A", "value": 200000},
        
        # Cycle 2: D -> E -> F -> G -> H -> I -> D (length 6, ignored)
        {"from_gstin": "D", "to_gstin": "E", "value": 200000},
        {"from_gstin": "E", "to_gstin": "F", "value": 200000},
        {"from_gstin": "F", "to_gstin": "G", "value": 200000},
        {"from_gstin": "G", "to_gstin": "H", "value": 200000},
        {"from_gstin": "H", "to_gstin": "I", "value": 200000},
        {"from_gstin": "I", "to_gstin": "D", "value": 200000},
    ])
    
    findings, graph_data = run(ds, [], None)
    
    assert len(graph_data.cycles) == 1
    assert set(graph_data.cycles[0]['nodes']) == {"A", "B", "C"}
    
    # Check findings
    assert len(findings) == 2
    f_sups = {f.supplier_id for f in findings}
    assert f_sups == {10, 11}
