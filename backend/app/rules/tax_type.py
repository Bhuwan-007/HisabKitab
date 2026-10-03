from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    business = dataset.business.iloc[0]
    our_state = business['state_code']
    
    sups = {s['id']: s for s in dataset.suppliers.to_dict('records')}
    
    for _, pb in dataset.purchase_books.iterrows():
        sup = sups.get(pb['supplier_id'])
        if not sup: continue
        
        sup_state = sup['state_code']
        is_intra = (sup_state == our_state)
        
        c, s, ig = float(pb['cgst']), float(pb['sgst']), float(pb['igst'])
        
        wrong = False
        if is_intra and ig > 0:
            wrong = True
        elif not is_intra and (c > 0 or s > 0):
            wrong = True
            
        if wrong:
            tax = c + s + ig
            findings.append(Finding(
                rule_id='R-TAX-03',
                issue_type='WRONG_TAX_TYPE',
                entity_type='purchase_invoice',
                entity_id=pb['id'],
                supplier_id=pb['supplier_id'],
                amount_at_stake=tax,
                confidence=0.95,
                evidence=[
                    Evidence('our_state', our_state, 'business'),
                    Evidence('supplier_state', sup_state, 'suppliers'),
                    Evidence('cgst', c, 'purchase_books'),
                    Evidence('sgst', s, 'purchase_books'),
                    Evidence('igst', ig, 'purchase_books')
                ],
                deadline=None,
                action='ASK_CREDIT_NOTE',
                bucket='NEEDS_FIX',
                reason="Wrong tax type (IGST vs CGST/SGST) applied based on state"
            ))
            
    return findings
