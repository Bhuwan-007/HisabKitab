from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "as_of_date" in res.json()

def test_seed():
    res = client.post("/api/data/seed", json={"seed": 42})
    assert res.status_code == 200

def test_upload():
    res = client.post(
        "/api/data/upload/purchase_books", 
        files={"file": ("test.csv", b"dummy data", "text/csv")}
    )
    assert res.status_code == 200

def test_run_recon():
    res = client.post("/api/reconcile/run")
    assert res.status_code == 200

def test_summary():
    res = client.get("/api/summary")
    assert res.status_code == 200

def test_recon_status():
    res = client.get("/api/reconciliation/status")
    assert res.status_code == 200

def test_records():
    res = client.get("/api/reconciliation/records")
    assert res.status_code == 200

def test_queue():
    res = client.get("/api/queue")
    assert res.status_code == 200
    assert len(res.json()) >= 12

def test_queue_detail():
    res = client.get("/api/queue/1")
    assert res.status_code == 200
    assert res.json()["id"] == 1

def test_queue_patch():
    res = client.patch("/api/queue/1", json={"status": "RESOLVED"})
    assert res.status_code == 200
    assert res.json()["status"] == "RESOLVED"

def test_queue_explain():
    res = client.post("/api/queue/1/explain")
    assert res.status_code == 200

def test_queue_draft():
    res = client.post("/api/queue/1/draft")
    assert res.status_code == 200

def test_suppliers():
    res = client.get("/api/suppliers")
    assert res.status_code == 200

def test_supplier_detail():
    res = client.get("/api/suppliers/1")
    assert res.status_code == 200

def test_graph():
    res = client.get("/api/graph")
    assert res.status_code == 200

def test_liability():
    res = client.get("/api/liability")
    assert res.status_code == 200

def test_audit():
    res = client.get("/api/audit")
    assert res.status_code == 200

def test_audit_verify():
    res = client.get("/api/audit/verify")
    assert res.status_code == 200

def test_evaluation():
    res = client.get("/api/evaluation")
    assert res.status_code == 200

def test_rules():
    res = client.get("/api/rules")
    assert res.status_code == 200
