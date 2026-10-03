import pandas as pd
from app.rules.base import Finding, Evidence

def score_suppliers(dataset, findings, cycles):
    scores = {}
    
    # Precompute metrics per supplier
    pb = dataset.purchase_books
    total_invs = pb.groupby('supplier_id').size().to_dict()
    
    # Missing in GSTR2B
    f_missing = [f for f in findings if f.issue_type == 'MISSING_IN_GSTR2B']
    missing_counts = {}
    for f in f_missing:
        missing_counts[f.supplier_id] = missing_counts.get(f.supplier_id, 0) + 1
        
    # Mismatch rate (amount, rate, duplicates)
    f_issues = [f for f in findings if f.issue_type in ['AMOUNT_MISMATCH', 'WRONG_TAX_RATE', 'DUPLICATE_INVOICE']]
    issue_counts = {}
    for f in f_issues:
        issue_counts[f.supplier_id] = issue_counts.get(f.supplier_id, 0) + 1
        
    # Circular trading nodes
    circular_suppliers = set()
    for cycle in cycles:
        for node in cycle['nodes']:
            # map GSTIN to supplier_id
            sup = dataset.suppliers[dataset.suppliers['gstin'] == node]
            if not sup.empty:
                circular_suppliers.add(sup.iloc[0]['id'])
                
    for _, s in dataset.suppliers.iterrows():
        sup_id = s['id']
        total_invoices = total_invs.get(sup_id, 0)
        
        factors = []
        
        if s['gstin_status'] == 'CANCELLED':
            factors.append({
                "name": "GSTIN cancelled",
                "weight": 100,
                "normalised": 1.0,
                "contribution": 100.0,
                "plain_text": "GSTIN is CANCELLED"
            })
            scores[sup_id] = {
                "score": 100.0,
                "factors": factors
            }
            continue
            
        # 1. Missed or late filings
        on_time = int(s['filings_last_6m_on_time']) if pd.notna(s['filings_last_6m_on_time']) else 6
        n_late = max(0, 6 - on_time) / 6.0
        factors.append({
            "name": "Missed or late filings in last 6 months",
            "weight": 30,
            "normalised": n_late,
            "contribution": round(30 * n_late, 2),
            "plain_text": f"{6 - on_time} out of 6 filings missed or late"
        })
        
        # 2. Missing in 2B
        missing = missing_counts.get(sup_id, 0)
        n_miss = min(missing / total_invoices, 1.0) if total_invoices > 0 else 0.0
        factors.append({
            "name": "Share of our invoices missing in GSTR-2B",
            "weight": 25,
            "normalised": n_miss,
            "contribution": round(25 * n_miss, 2),
            "plain_text": f"{missing} out of {total_invoices} invoices missing"
        })
        
        # 3. Avg filing delay
        delay = float(s['avg_filing_delay_days']) if pd.notna(s['avg_filing_delay_days']) else 0.0
        n_delay = min(delay / 30.0, 1.0)
        factors.append({
            "name": "Average filing delay",
            "weight": 15,
            "normalised": n_delay,
            "contribution": round(15 * n_delay, 2),
            "plain_text": f"Average delay of {delay} days"
        })
        
        # 4. Mismatch rate
        issues = issue_counts.get(sup_id, 0)
        n_iss = min(issues / total_invoices, 1.0) if total_invoices > 0 else 0.0
        factors.append({
            "name": "Mismatch rate with us",
            "weight": 15,
            "normalised": n_iss,
            "contribution": round(15 * n_iss, 2),
            "plain_text": f"{issues} issues across {total_invoices} invoices"
        })
        
        # 5. Circular trading
        in_loop = 1.0 if sup_id in circular_suppliers else 0.0
        factors.append({
            "name": "In a flagged circular-trading loop",
            "weight": 15,
            "normalised": in_loop,
            "contribution": round(15 * in_loop, 2),
            "plain_text": "Flagged" if in_loop > 0 else "Not flagged"
        })
        
        score = sum(f['contribution'] for f in factors)
        scores[sup_id] = {
            "score": round(score, 2),
            "factors": sorted(factors, key=lambda x: x['contribution'], reverse=True)
        }
        
    return scores
