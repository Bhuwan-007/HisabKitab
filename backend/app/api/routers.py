import json
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from ..schemas import (
    HealthResponse, QueueItem, QueueDetail, SummaryResponse, ReconStatusResponse,
    RecordsPage, SupplierSummary, SupplierDetail, GraphResponse, LiabilityResponse,
    AuditRow, AuditVerify, EvaluationResponse, RulesResponse, RunSummary, QueueStatus
)
from ..config import config

router = APIRouter()

def load_fixture(name: str):
    path = os.path.join(os.path.dirname(__file__), "fixtures", f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# STUB: replace in stage N

_QUEUE_ITEMS = load_fixture("queue")
_QUEUE_DICT = {item["id"]: item for item in _QUEUE_ITEMS}

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "ok",
        "as_of_date": config.AS_OF_DATE,
        "period": config.OPEN_PERIOD,
        "llm_provider": config.LLM_PROVIDER
    }

class SeedRequest(BaseModel):
    seed: Optional[int] = None

@router.post("/data/seed")
def seed_data(req: SeedRequest = None):
    return {"status": "seeded"}

@router.post("/data/upload/{kind}")
def upload_data(kind: str, file: UploadFile = File(...)):
    return {"status": "uploaded", "kind": kind, "filename": file.filename}

@router.post("/reconcile/run", response_model=RunSummary)
def run_recon():
    return load_fixture("run_summary")

@router.get("/summary", response_model=SummaryResponse)
def get_summary(period: str = None):
    return load_fixture("summary")

@router.get("/reconciliation/status", response_model=ReconStatusResponse)
def get_recon_status(source: str = None):
    return load_fixture("status")

@router.get("/reconciliation/records", response_model=RecordsPage)
def get_recon_records(source: str = None, status: str = None, page: int = 1):
    return load_fixture("records")

@router.get("/queue", response_model=List[QueueItem])
def get_queue(bucket: str = None, type: str = None, severity: str = None, status: str = None, period: str = None, sort: str = "priority"):
    return list(_QUEUE_DICT.values())

@router.get("/queue/{id}", response_model=QueueDetail)
def get_queue_detail(id: int):
    if id not in _QUEUE_DICT:
        raise HTTPException(status_code=404, detail="Not found")
    return _QUEUE_DICT[id]

class QueuePatch(BaseModel):
    status: QueueStatus

@router.patch("/queue/{id}", response_model=QueueItem)
def update_queue(id: int, req: QueuePatch):
    if id not in _QUEUE_DICT:
        raise HTTPException(status_code=404, detail="Not found")
    _QUEUE_DICT[id]["status"] = req.status
    return _QUEUE_DICT[id]

@router.post("/queue/{id}/explain", response_model=QueueDetail)
def explain_queue(id: int):
    if id not in _QUEUE_DICT:
        raise HTTPException(status_code=404, detail="Not found")
    _QUEUE_DICT[id]["explanation"] = "Generated explanation..."
    return _QUEUE_DICT[id]

@router.post("/queue/{id}/draft", response_model=QueueDetail)
def draft_queue(id: int):
    if id not in _QUEUE_DICT:
        raise HTTPException(status_code=404, detail="Not found")
    _QUEUE_DICT[id]["draft"] = "Draft message..."
    return _QUEUE_DICT[id]

@router.get("/suppliers", response_model=List[SupplierSummary])
def get_suppliers():
    return load_fixture("suppliers")

@router.get("/suppliers/{id}", response_model=SupplierDetail)
def get_supplier_detail(id: int):
    return load_fixture("supplier_detail")

@router.get("/graph", response_model=GraphResponse)
def get_graph():
    return load_fixture("graph")

@router.get("/liability", response_model=LiabilityResponse)
def get_liability(period: str = None):
    return load_fixture("liability")

@router.get("/audit", response_model=List[AuditRow])
def get_audit(limit: int = 50):
    return load_fixture("audit")

@router.get("/audit/verify", response_model=AuditVerify)
def verify_audit():
    return load_fixture("audit_verify")

@router.get("/evaluation", response_model=EvaluationResponse)
def get_eval():
    return load_fixture("eval")

@router.get("/rules", response_model=RulesResponse)
def get_rules():
    return load_fixture("rules")
