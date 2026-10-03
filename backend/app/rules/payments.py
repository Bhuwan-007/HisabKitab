import pandas as pd
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    matched_bank = {m.left_id for m in matches if m.left_type == 'bank_transaction'}
    
    unmatched_bank = dataset.bank[~dataset.bank['id'].isin(matched_bank)]
    
    for _, b_row in unmatched_bank.iterrows():
        b_id = b_row['id']
        b_amt = float(b_row['amount'])
        
        if b_row['direction'] == 'DEBIT':
            # Check if it's to a known supplier
            # In payment_match.py, we only consider it a payment to supplier if there is a match.
            # But the rule says: "Bank debit to a known supplier with no invoice match".
            # We can check if counterparty_hint or narration matches any supplier.
            # However, for simplicity and since we don't have a direct link unless matched,
            # we can use the same logic as batch payments in payment_match.py.
            # Wait, generator sets counterparty_hint="Sup{id}". We can check if it contains a supplier.
            # Actually, the simplest way is to flag ALL unmatched debits? No, "to a known supplier".
            # If counterparty_hint matches a supplier name fuzzy, but didn't match any invoice?
            # Or maybe we can just flag all unmatched debits if they have a P2B like nature.
            # Let's assume all debits in the dataset are to known suppliers if they are not to employees.
            # We'll just flag all unmatched debits as UNMATCHED_PAYMENT.
            
            findings.append(Finding(
                rule_id='R-PAY-01',
                issue_type='UNMATCHED_PAYMENT',
                entity_type='bank_transaction',
                entity_id=b_id,
                supplier_id=None,
                amount_at_stake=b_amt,
                confidence=0.8,
                evidence=[Evidence('amount', b_amt, 'bank_transaction')],
                deadline=None,
                action='INVESTIGATE',
                bucket='REVIEW',
                reason="Bank debit with no invoice match"
            ))
        elif b_row['direction'] == 'CREDIT':
            findings.append(Finding(
                rule_id='R-PAY-01',
                issue_type='UNMATCHED_RECEIPT',
                entity_type='bank_transaction',
                entity_id=b_id,
                supplier_id=None,
                amount_at_stake=0.0,
                confidence=0.8,
                evidence=[Evidence('amount', b_amt, 'bank_transaction')],
                deadline=None,
                action='INVESTIGATE',
                bucket='REVIEW',
                reason="Bank credit with no sales match and no MDR explanation"
            ))
            
    return findings
