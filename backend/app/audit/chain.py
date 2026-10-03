import hashlib
import json
from datetime import datetime
from sqlmodel import Session, select
from app.models import AuditLog
from app.config import config

def canonical_json(data: dict) -> str:
    return json.dumps(data, separators=(',', ':'), sort_keys=True)

def append_audit(session: Session, actor: str, action: str, entity_type: str, entity_id: int, payload: dict):
    # Fetch last row
    last_log = session.exec(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).first()
    prev_hash = last_log.hash if last_log else "GENESIS"
    
    ts = datetime.utcnow().isoformat() + "Z"
    
    data = {
        "ts": ts,
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload
    }
    data_str = canonical_json(data)
    
    current_hash = hashlib.sha256((prev_hash + data_str).encode('utf-8')).hexdigest()
    
    log = AuditLog(
        ts=ts,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload_json=json.dumps(payload),
        prev_hash=prev_hash,
        hash=current_hash
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

def verify_chain(session: Session):
    logs = session.exec(select(AuditLog).order_by(AuditLog.id.asc())).all()
    
    prev_hash = "GENESIS"
    for log in logs:
        if log.prev_hash != prev_hash:
            return {"valid": False, "broken_at_id": log.id}
            
        payload = json.loads(log.payload_json) if log.payload_json else {}
        data = {
            "ts": log.ts,
            "actor": log.actor,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "payload": payload
        }
        data_str = canonical_json(data)
        
        expected_hash = hashlib.sha256((prev_hash + data_str).encode('utf-8')).hexdigest()
        
        if log.hash != expected_hash:
            return {"valid": False, "broken_at_id": log.id}
            
        prev_hash = log.hash
        
    return {"valid": True, "broken_at_id": None}
