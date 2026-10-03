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
    
    matches = match_invoices(ds)
    findings = run_all_tax_rules(ds, matches, config)
    
    f_counts = collections.Counter([f.issue_type for f in findings])
    
    with Session(engine) as session:
        gts = session.exec(select(GroundTruth)).all()
        gt_counts = collections.Counter([gt.injected_issue_type for gt in gts if gt.injected_issue_type])
        
    print(f"{'Issue Type':<30} | {'Found':<8} | {'Ground Truth':<12}")
    print("-" * 55)
    
    all_types = set(f_counts.keys()).union(set(gt_counts.keys()))
    for t in sorted(all_types):
        # We only care about the tax and match rules for this stage
        relevant_rules = {
            "MISSING_IN_GSTR2B", "MISSING_IN_BOOKS", "AMOUNT_MISMATCH",
            "SUPPLIER_GSTIN_CANCELLED", "WRONG_TAX_RATE", "WRONG_TAX_TYPE",
            "DUPLICATE_INVOICE", "PERIOD_CUTOFF", "ROUNDING_DIFF"
        }
        if t in relevant_rules:
            print(f"{t:<30} | {f_counts.get(t, 0):<8} | {gt_counts.get(t, 0):<12}")

if __name__ == "__main__":
    main()
