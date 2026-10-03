from fastapi.testclient import TestClient
from app.main import app
from app.pipeline import run_reconciliation
from sqlmodel import Session
from app.db import engine
from app.config import config

with Session(engine) as s:
    run_reconciliation(s, config.OPEN_PERIOD)

client = TestClient(app)
r = client.get("/api/summary")
data = r.json()

print("Summary Endpoint Data:")
print("safe_to_claim:", data['safe_to_claim'])
print("at_risk:", data['at_risk'])
print("needs_fix:", data['needs_fix'])
print("total:", data['safe_to_claim'] + data['at_risk'] + data['needs_fix'])
print("liability:", data['liability'])
print("status_breakdown:", data['status_breakdown'])

print("\nTop 5 queue length:", len(data['top5_queue']))
for i, q in enumerate(data['top5_queue']):
    print(f"{i+1}: {q['issue_type']} - score {q['priority_score']} - entity: {q['entity']}")
