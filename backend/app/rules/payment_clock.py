import pandas as pd
from datetime import timedelta
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    as_of = pd.to_datetime(cfg.AS_OF_DATE).date()
    
    # Calculate payments for each purchase invoice
    paid_amounts = {}
    for m in matches:
        if m.left_type == 'bank_transaction' and m.right_type == 'purchase_books':
            bank_id = m.left_id
            pb_id = m.right_id
            
            b_row = dataset.bank[dataset.bank['id'] == bank_id].iloc[0]
            b_amt = float(b_row['amount'])
            
            # If batch payment, the amount is split?
            # Wait, batch payment matches multiple invoices.
            # But the match_type is BATCH_PAYMENT. In payment_match.py, how is it assigned?
            # It matches the FULL bank amount to the batch. BUT wait, how much is paid per invoice?
            # It fully pays the matched invoices in the batch. So we can just add the invoice total to the paid amount?
            # Actually, to be safe, let's just consider the invoice fully paid if it's matched to a BATCH_PAYMENT, 
            # or we can sum the matched bank transactions. But one bank transaction is matched to MULTIPLE invoices.
            # So `b_amt` is the sum. We shouldn't add `b_amt` to each invoice!
            # Instead, we should just mark the invoice as fully paid, or add the invoice's own total as paid.
            pb_row = dataset.purchase_books[dataset.purchase_books['id'] == pb_id].iloc[0]
            if m.match_type == 'BATCH_PAYMENT':
                paid_amounts[pb_id] = paid_amounts.get(pb_id, 0.0) + float(pb_row['total'])
            else:
                paid_amounts[pb_id] = paid_amounts.get(pb_id, 0.0) + b_amt
                
    for _, pb in dataset.purchase_books.iterrows():
        pb_id = pb['id']
        total = float(pb['total'])
        if total <= 0:
            continue
            
        paid = paid_amounts.get(pb_id, 0.0)
        unpaid_share = max(0.0, 1.0 - (paid / total))
        
        inv_date = pd.to_datetime(pb['invoice_date']).date()
        days_elapsed = (as_of - inv_date).days
        deadline = inv_date + timedelta(days=cfg.PAYMENT_WINDOW_DAYS)
        days_left = cfg.PAYMENT_WINDOW_DAYS - days_elapsed
        
        if unpaid_share > 0.01 and days_left <= cfg.PAYMENT_WARN_DAYS:
            tax = float(pb['cgst'] + pb['sgst'] + pb['igst'])
            stake = tax * unpaid_share
            
            action = 'PAY_NOW'
            title = "Pay supplier before the 180-day limit"
            if days_left < 0:
                action = 'REVERSE_ITC'
                title = "180-day limit passed; credit must be reversed"
                
            unpaid_amt = round(total * unpaid_share, 2)
            
            findings.append(Finding(
                rule_id='R-CLK-01',
                issue_type='PAYMENT_180_DAY_RISK',
                entity_type='purchase_invoice',
                entity_id=pb_id,
                supplier_id=pb['supplier_id'],
                amount_at_stake=stake,
                confidence=1.0,
                evidence=[
                    Evidence('invoice_date', str(inv_date), 'purchase_books'),
                    Evidence('deadline', str(deadline), 'computed'),
                    Evidence('days_left', days_left, 'computed'),
                    Evidence('paid_amount', paid, 'computed'),
                    Evidence('unpaid_amount', unpaid_amt, 'computed'),
                    Evidence('tax', tax, 'purchase_books'),
                    Evidence('unpaid_share', unpaid_share, 'computed')
                ],
                deadline=deadline,
                action=action,
                bucket='AT_RISK',
                reason=title
            ))
            
    return findings
