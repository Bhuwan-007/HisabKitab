import pandas as pd
from datetime import date, timedelta
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    # Pre-compute matches
    matched_pb = set(m.left_id for m in matches if m.left_type == 'purchase_books' and m.right_type == 'gstr2b')
    matched_g2b = set(m.right_id for m in matches if m.left_type == 'purchase_books' and m.right_type == 'gstr2b')
    
    amount_matches = [m for m in matches if m.left_type == 'purchase_books' and m.right_type == 'gstr2b' and m.match_type == 'AMOUNT']

    # Suppliers dict
    sups = {s['id']: s for s in dataset.suppliers.to_dict('records')}
    
    for _, pb in dataset.purchase_books.iterrows():
        inv_date = pd.to_datetime(pb['invoice_date']).date()
        tax = pb['cgst'] + pb['sgst'] + pb['igst']
        
        # R-ITC-01 Cancelled or suspended supplier
        sup = sups.get(pb['supplier_id'])
        if sup and sup['gstin_status'] in ['CANCELLED', 'SUSPENDED'] and pd.notna(sup['status_changed_on']):
            changed_on = pd.to_datetime(sup['status_changed_on']).date()
            if inv_date >= changed_on:
                findings.append(Finding(
                    rule_id='R-ITC-01',
                    issue_type='SUPPLIER_GSTIN_CANCELLED',
                    entity_type='purchase_invoice',
                    entity_id=pb['id'],
                    supplier_id=pb['supplier_id'],
                    amount_at_stake=tax,
                    confidence=1.0,
                    evidence=[
                        Evidence('gstin_status', sup['gstin_status'], 'suppliers'),
                        Evidence('status_changed_on', str(changed_on), 'suppliers'),
                        Evidence('invoice_date', str(inv_date), 'purchase_books')
                    ],
                    deadline=pd.to_datetime(cfg.AS_OF_DATE).date(),
                    action='HOLD_PAYMENT',
                    bucket='AT_RISK',
                    reason=f"GSTIN is {sup['gstin_status']} since {changed_on}"
                ))
        
        # R-MATCH-01 Missing in GSTR-2B
        if pb['id'] not in matched_pb:
            # Deadline: GSTR1_DUE_DAY_OF_MONTH of the next month
            # Calculate next month
            m = inv_date.month
            y = inv_date.year
            if m == 12:
                next_m = 1
                next_y = y + 1
            else:
                next_m = m + 1
                next_y = y
            deadline = date(next_y, next_m, cfg.GSTR1_DUE_DAY_OF_MONTH)
            
            findings.append(Finding(
                rule_id='R-MATCH-01',
                issue_type='MISSING_IN_GSTR2B',
                entity_type='purchase_invoice',
                entity_id=pb['id'],
                supplier_id=pb['supplier_id'],
                amount_at_stake=tax,
                confidence=0.95,
                evidence=[
                    Evidence('invoice_tax', tax, 'purchase_books')
                ],
                deadline=deadline,
                action='CONTACT_SUPPLIER',
                bucket='AT_RISK',
                reason="Unmatched purchase invoice"
            ))
            
    # R-MATCH-02 Missing in books
    for _, g2b in dataset.gstr2b.iterrows():
        if g2b['id'] not in matched_g2b:
            tax = g2b['cgst'] + g2b['sgst'] + g2b['igst']
            
            # Find supplier ID from gstin
            sup_id = None
            for s in sups.values():
                if s['gstin'] == g2b['supplier_gstin']:
                    sup_id = s['id']
                    break
                    
            findings.append(Finding(
                rule_id='R-MATCH-02',
                issue_type='MISSING_IN_BOOKS',
                entity_type='gstr2b_entry',
                entity_id=g2b['id'],
                supplier_id=sup_id,
                amount_at_stake=tax,
                confidence=0.9,
                evidence=[
                    Evidence('gstr2b_tax', tax, 'gstr2b_entries')
                ],
                deadline=None,
                action='RECORD_INVOICE',
                bucket='NEEDS_FIX',
                reason="Unmatched GSTR-2B entry"
            ))

    # R-MATCH-03 Low-confidence match
    for m in amount_matches:
        findings.append(Finding(
            rule_id='R-MATCH-03',
            issue_type='AMOUNT_MISMATCH',
            entity_type='purchase_invoice',
            entity_id=m.left_id,
            supplier_id=dataset.purchase_books[dataset.purchase_books['id'] == m.left_id].iloc[0]['supplier_id'],
            amount_at_stake=0.0,
            confidence=0.55,
            evidence=[
                Evidence('confidence', 0.55, 'matches'),
                Evidence('match_type', 'AMOUNT', 'matches')
            ],
            deadline=None,
            action='INVESTIGATE',
            bucket='REVIEW',
            reason="matched on amount only, invoice numbers differ"
        ))

    return findings
