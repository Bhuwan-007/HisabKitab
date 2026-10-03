import pandas as pd
from calendar import monthrange
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    # Pre-process matches
    g2b_matches = {}
    for m in matches:
        if m.left_type == 'purchase_books' and m.right_type == 'gstr2b':
            g2b_matches[m.left_id] = m.right_id
            
    bank_matches = {}
    for m in matches:
        if m.left_type == 'bank_transaction' and m.right_type == 'purchase_books':
            if m.right_id not in bank_matches:
                bank_matches[m.right_id] = []
            bank_matches[m.right_id].append(m.left_id)
            
    g2b_dict = dataset.gstr2b.set_index('id').to_dict('index')
    bank_dict = dataset.bank.set_index('id').to_dict('index')
    
    for _, pb in dataset.purchase_books.iterrows():
        inv_date = pd.to_datetime(pb['invoice_date']).date()
        
        # Check if in last 3 days of month
        _, last_day = monthrange(inv_date.year, inv_date.month)
        if inv_date.day >= last_day - 2:
            # Check conditions
            inv_month_str = inv_date.strftime("%Y-%m")
            
            cutoff_issue = False
            reasons = []
            
            if pb['itc_period'] > inv_month_str:
                cutoff_issue = True
                reasons.append("itc_period in next month")
                
            # Check GSTR-2B period
            g2b_id = g2b_matches.get(pb['id'])
            if g2b_id and g2b_id in g2b_dict:
                g2b = g2b_dict[g2b_id]
                if g2b['return_period'] > inv_month_str:
                    cutoff_issue = True
                    reasons.append("GSTR-2B return_period in next month")
                    
            # Check payment date
            p_ids = bank_matches.get(pb['id'], [])
            for p_id in p_ids:
                if p_id in bank_dict:
                    p_date = pd.to_datetime(bank_dict[p_id]['txn_date']).date()
                    if p_date.strftime("%Y-%m") > inv_month_str:
                        cutoff_issue = True
                        reasons.append("payment date in next month")
                        
            if cutoff_issue:
                findings.append(Finding(
                    rule_id='R-CUT-01',
                    issue_type='PERIOD_CUTOFF',
                    entity_type='purchase_invoice',
                    entity_id=pb['id'],
                    supplier_id=pb['supplier_id'],
                    amount_at_stake=0.0,
                    confidence=0.8,
                    evidence=[
                        Evidence('invoice_date', str(inv_date), 'purchase_books'),
                        Evidence('itc_period', pb['itc_period'], 'purchase_books')
                    ],
                    deadline=None,
                    action='INVESTIGATE',
                    bucket='REVIEW',
                    reason="timing difference between periods; confirm which period the credit belongs to"
                ))

    # R-RND-01 Rounding
    pb_dict = dataset.purchase_books.set_index('id').to_dict('index')
    for m in matches:
        if m.left_type == 'purchase_books' and m.right_type == 'gstr2b':
            pb = pb_dict.get(m.left_id)
            g2b = g2b_dict.get(m.right_id)
            if pb and g2b:
                pb_tax = float(pb['cgst'] + pb['sgst'] + pb['igst'])
                g2b_tax = float(g2b['cgst'] + g2b['sgst'] + g2b['igst'])
                diff = abs(pb_tax - g2b_tax)
                
                # We know config.ROUNDING_TOLERANCE is usually 0, but let's assume > 0 diff
                if diff > 0.0 and diff <= cfg.ROUNDING_TOLERANCE:
                    findings.append(Finding(
                        rule_id='R-RND-01',
                        issue_type='ROUNDING_DIFF',
                        entity_type='purchase_invoice',
                        entity_id=m.left_id,
                        supplier_id=pb['supplier_id'],
                        amount_at_stake=0.0,
                        confidence=1.0,
                        evidence=[
                            Evidence('books_tax', pb_tax, 'purchase_books'),
                            Evidence('gstr2b_tax', g2b_tax, 'gstr2b_entries'),
                            Evidence('difference', diff, 'computed')
                        ],
                        deadline=None,
                        action='AUTO_RESOLVED',
                        bucket='AUTO_RESOLVED',
                        reason="Rounding difference within 1 rupee"
                    ))

    return findings
