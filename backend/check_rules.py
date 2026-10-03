import collections
from sqlmodel import Session, select
from app.db import engine
from app.models import GroundTruth
from app.ingest.loaders import load_all
from app.matching.invoice_match import match_invoices
from app.rules import run_all_tax_rules
from app.config import config

def main():
    ds = load_all()
    
    from app.matching.payment_match import match_payments
    matches = match_invoices(ds)
    p_matches = match_payments(ds)
    matches.extend(p_matches)
    
    findings = run_all_tax_rules(ds, matches, config)
    from app.rules import run_all_payment_rules
    p_findings = run_all_payment_rules(ds, matches, config)
    findings.extend(p_findings)
    
    from app.risk import run_risk_layer
    risk_result = run_risk_layer(ds, findings, config)
    findings.extend(risk_result.new_findings)
    
    f_counts = collections.Counter([f.issue_type for f in findings])
    
    with Session(engine) as session:
        gts = session.exec(select(GroundTruth)).all()
        gt_counts = collections.Counter([gt.injected_issue_type for gt in gts if gt.injected_issue_type])
        
    print(f"{'Issue Type':<30} | {'Found':<8} | {'Ground Truth':<12}")
    print("-" * 55)
    
    all_types = set(f_counts.keys()).union(set(gt_counts.keys()))
    for t in sorted(all_types):
        if t:
            print(f"{t:<30} | {f_counts.get(t, 0):<8} | {gt_counts.get(t, 0):<12}")
            
    print("\n--- Top 5 Suppliers by Score ---")
    scores = risk_result.supplier_scores
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    for sup_id, data in sorted_scores[:5]:
        sup = ds.suppliers[ds.suppliers['id'] == sup_id].iloc[0]
        print(f"Supplier: {sup['name']} (ID: {sup_id}) - Score: {data['score']}")
        for factor in data['factors'][:2]:
            print(f"  - {factor['name']}: {factor['contribution']} ({factor['plain_text']})")
            
    print("\n--- Cycles Found ---")
    print(f"Cycles found: {len(risk_result.graph_data.cycles)}")
    
if __name__ == "__main__":
    main()
