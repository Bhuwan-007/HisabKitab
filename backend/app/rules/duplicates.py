import pandas as pd
from rapidfuzz import fuzz
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    # We group purchase_books by supplier_id
    sups = {s['id']: s for s in dataset.suppliers.to_dict('records')}
    
    groups = dataset.purchase_books.groupby('supplier_id')
    for supplier_id, group in groups:
        # Exact duplicates
        # Group by invoice_no_norm
        exact_groups = group.groupby('invoice_no_norm')
        for norm, g in exact_groups:
            if len(g) > 1:
                # Sort by invoice_date, then id
                g_sorted = g.sort_values(['invoice_date', 'id'])
                # keep earliest
                orig = g_sorted.iloc[0]
                for _, dup in g_sorted.iloc[1:].iterrows():
                    tax = float(dup['cgst'] + dup['sgst'] + dup['igst'])
                    findings.append(Finding(
                        rule_id='R-DUP-01',
                        issue_type='DUPLICATE_INVOICE',
                        entity_type='purchase_invoice',
                        entity_id=dup['id'],
                        supplier_id=supplier_id,
                        amount_at_stake=tax,
                        confidence=1.0,
                        evidence=[
                            Evidence('duplicate_of', orig['id'], 'purchase_books'),
                            Evidence('invoice_no_norm', norm, 'purchase_books')
                        ],
                        deadline=None,
                        action='REMOVE_DUPLICATE',
                        bucket='NEEDS_FIX',
                        reason="Exact duplicate invoice number in books"
                    ))
                    
        # Fuzzy duplicates
        # same supplier, token_sort_ratio >= 90 on raw numbers, same taxable value, dates within 3 days.
        # We must exclude already flagged exact duplicates.
        exact_flagged = {f.entity_id for f in findings if f.issue_type == 'DUPLICATE_INVOICE'}
        rem = group[~group['id'].isin(exact_flagged)]
        
        # Sort by date, then id to keep earliest
        rem = rem.sort_values(['invoice_date', 'id'])
        
        fuzzy_flagged = set()
        for i, row1 in rem.iterrows():
            if row1['id'] in fuzzy_flagged: continue
            
            for j, row2 in rem.iterrows():
                if row1['id'] == row2['id']: continue
                if row2['id'] in fuzzy_flagged: continue
                
                # Check conditions
                if abs(float(row1['taxable_value'] - row2['taxable_value'])) > cfg.ROUNDING_TOLERANCE:
                    continue
                date_diff = abs((pd.to_datetime(row1['invoice_date']) - pd.to_datetime(row2['invoice_date'])).days)
                if date_diff > 3:
                    continue
                    
                score = fuzz.token_sort_ratio(str(row1['invoice_no_raw']), str(row2['invoice_no_raw']))
                if score >= 90:
                    tax = float(row2['cgst'] + row2['sgst'] + row2['igst'])
                    findings.append(Finding(
                        rule_id='R-DUP-01',
                        issue_type='DUPLICATE_INVOICE',
                        entity_type='purchase_invoice',
                        entity_id=row2['id'],
                        supplier_id=supplier_id,
                        amount_at_stake=tax,
                        confidence=0.85,
                        evidence=[
                            Evidence('fuzzy_duplicate_of', row1['id'], 'purchase_books'),
                            Evidence('similarity_score', score, 'rapidfuzz')
                        ],
                        deadline=None,
                        action='REMOVE_DUPLICATE',
                        bucket='NEEDS_FIX',
                        reason="Fuzzy duplicate based on similar invoice number and amounts"
                    ))
                    fuzzy_flagged.add(row2['id'])

    return findings
