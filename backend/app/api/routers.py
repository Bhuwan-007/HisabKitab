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
from sqlmodel import Session, select, func
from app.db import engine
from app.models import Issue, RecordStatus, ReconRun, AuditLog, SupplierScore, GroundTruth
from app.pipeline import run_reconciliation
from app.decision.liability import compute_liability
from app.ingest.loaders import load_all
from app.eval.evaluate import evaluate_run
from app.audit.chain import append_audit, verify_chain

router = APIRouter()

def load_fixture(name: str):
    path = os.path.join(os.path.dirname(__file__), "fixtures", f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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
    from app.seed.generator import generate_data
    generate_data()
    return {"status": "seeded"}

@router.post("/data/upload/{kind}")
def upload_data(kind: str, file: UploadFile = File(...)):
    return {"status": "uploaded", "kind": kind, "filename": file.filename}

class RunRequest(BaseModel):
    period: Optional[str] = None

@router.post("/reconcile/run", response_model=RunSummary)
def run_recon(req: RunRequest = None):
    period = req.period if req and req.period else config.OPEN_PERIOD
    with Session(engine) as session:
        res = run_reconciliation(session, period)
        return res

@router.get("/summary", response_model=SummaryResponse)
def get_summary(period: str = None):
    return load_fixture("summary")

@router.get("/reconciliation/status", response_model=ReconStatusResponse)
def get_recon_status(source: str = None):
    return load_fixture("status")

@router.get("/reconciliation/records", response_model=RecordsPage)
def get_recon_records(source: str = None, status: str = None, page: int = 1):
    return load_fixture("records")

def _format_issue(issue: Issue) -> dict:
    d = {k: getattr(issue, k) for k in Issue.model_fields.keys()}
    d["entity"] = {
        "type": issue.entity_type,
        "id": issue.entity_id,
        "supplier_id": issue.supplier_id
    }
    d["evidence"] = json.loads(issue.evidence_json) if issue.evidence_json else []
    if getattr(issue, "deadline", None):
        d["deadline"] = issue.deadline.isoformat()
    d["draft"] = getattr(issue, "draft_body", None)
    return d

@router.get("/queue", response_model=List[QueueItem])
def get_queue(bucket: str = None, type: str = None, severity: str = None, status: str = None, period: str = None, sort: str = "priority"):
    period = period or config.OPEN_PERIOD
    with Session(engine) as session:
        run = session.exec(select(ReconRun).where(ReconRun.period == period).order_by(ReconRun.id.desc()).limit(1)).first()
        if not run:
            return []
            
        q = select(Issue).where(Issue.run_id == run.id)
        if bucket:
            q = q.where(Issue.bucket == bucket)
        if type:
            q = q.where(Issue.issue_type == type)
        if severity:
            q = q.where(Issue.severity == severity)
        if status:
            q = q.where(Issue.status == status)
            
        issues = session.exec(q).all()
        # Default behavior: hide AUTO_RESOLVED unless specifically requested
        if not bucket and not status:
            issues = [i for i in issues if i.bucket != 'AUTO_RESOLVED']
            
        issues.sort(key=lambda x: (x.priority_score or 0), reverse=True)
        return [_format_issue(i) for i in issues]

@router.get("/queue/{id}", response_model=QueueDetail)
def get_queue_detail(id: int):
    with Session(engine) as session:
        issue = session.exec(select(Issue).where(Issue.id == id)).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Not found")
        return _format_issue(issue)

class QueuePatch(BaseModel):
    status: QueueStatus

@router.patch("/queue/{id}", response_model=QueueItem)
def update_queue(id: int, req: QueuePatch):
    with Session(engine) as session:
        issue = session.exec(select(Issue).where(Issue.id == id)).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Not found")
        
        old_status = issue.status
        issue.status = req.status
        session.add(issue)
        session.commit()
        session.refresh(issue)
        
        append_audit(session, "user", "STATUS_CHANGED", "issue", issue.id, {"old": old_status, "new": req.status})
        
        return _format_issue(issue)

@router.post("/queue/{id}/explain", response_model=QueueDetail)
def explain_queue(id: int):
    with Session(engine) as session:
        issue = session.exec(select(Issue).where(Issue.id == id)).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Not found")
            
        issue.explanation = issue.plain_reason
        session.add(issue)
        session.commit()
        session.refresh(issue)
        append_audit(session, "system", "EXPLANATION_GENERATED", "issue", issue.id, {})
        return _format_issue(issue)

@router.post("/queue/{id}/draft", response_model=QueueDetail)
def draft_queue(id: int):
    with Session(engine) as session:
        issue = session.exec(select(Issue).where(Issue.id == id)).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Not found")
            
        issue.draft_subject = "Action Required"
        issue.draft_body = issue.plain_reason
        session.add(issue)
        session.commit()
        session.refresh(issue)
        append_audit(session, "system", "DRAFT_GENERATED", "issue", issue.id, {})
        return _format_issue(issue)

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
    period = period or config.OPEN_PERIOD
    with Session(engine) as session:
        run = session.exec(select(ReconRun).where(ReconRun.period == period).order_by(ReconRun.id.desc()).limit(1)).first()
        if not run:
            return load_fixture("liability")
            
        issues = session.exec(select(Issue).where(Issue.run_id == run.id)).all()
        ds = load_all()
        return compute_liability(ds, issues, period)["liability"]

@router.get("/audit", response_model=List[AuditRow])
def get_audit(limit: int = 50):
    with Session(engine) as session:
        logs = session.exec(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
        return logs

@router.get("/audit/verify", response_model=AuditVerify)
def do_verify_audit():
    with Session(engine) as session:
        return verify_chain(session)

@router.get("/evaluation", response_model=EvaluationResponse)
def get_eval():
    period = config.OPEN_PERIOD
    with Session(engine) as session:
        run = session.exec(select(ReconRun).where(ReconRun.period == period).order_by(ReconRun.id.desc()).limit(1)).first()
        if not run:
            return load_fixture("eval")
        ev = evaluate_run(session, run.id)
        return {"metrics": ev["by_type"]}

@router.get("/rules", response_model=RulesResponse)
def get_rules():
    return load_fixture("rules")
