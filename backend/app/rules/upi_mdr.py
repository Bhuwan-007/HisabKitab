import pandas as pd
from app.rules.base import Finding, Evidence

def get_mdr_fee(b_row, amount, cfg):
    if b_row['channel'] != 'UPI' or b_row['txn_kind'] != 'P2M':
        return 0.0
    
    b_date_str = pd.to_datetime(b_row['txn_date']).strftime("%Y-%m-%d")
    if b_date_str < str(cfg.UPI_MDR_EFFECTIVE):
        return 0.0
        
    if amount <= getattr(cfg, 'UPI_MDR_THRESHOLD', 2000.0):
        return 0.0
        
    if getattr(cfg, 'UPI_MDR_EXEMPT_MERCHANT', False):
        return 0.0
        
    fee = round(amount * getattr(cfg, 'UPI_MDR_RATE', 0.004), 2)
    return min(fee, getattr(cfg, 'UPI_MDR_CAP', 300.0))

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    for m in matches:
        if m.match_type == 'MDR_ADJUSTED':
            sales_id = m.right_id
            bank_id = m.left_id
            
            s_row = dataset.sales[dataset.sales['id'] == sales_id].iloc[0]
            b_row = dataset.bank[dataset.bank['id'] == bank_id].iloc[0]
            
            s_amt = float(s_row['total'])
            b_amt = float(b_row['amount'])
            fee = m.diffs.get("mdr_fee", 0.0)
            
            findings.append(Finding(
                rule_id='R-UPI-01',
                issue_type='UPI_MDR_ADJUSTED',
                entity_type='bank_transaction',
                entity_id=bank_id,
                supplier_id=None,
                amount_at_stake=0.0,
                confidence=1.0,
                evidence=[
                    Evidence('description', f"invoice {s_amt}, fee {fee}, deposit {b_amt}", 'computed'),
                    Evidence('mdr_fee', fee, 'computed')
                ],
                deadline=None,
                action='AUTO_RESOLVED',
                bucket='AUTO_RESOLVED',
                reason="UPI MDR fee correctly accounts for short settlement"
            ))
            
        elif m.match_type == 'UPI_UNEXPLAINED_SHORT':
            bank_id = m.left_id
            diff = m.diffs.get("amount_diff", 0.0)
            
            findings.append(Finding(
                rule_id='R-UPI-01',
                issue_type='UPI_SHORT_SETTLEMENT_UNEXPLAINED',
                entity_type='bank_transaction',
                entity_id=bank_id,
                supplier_id=None,
                amount_at_stake=diff,
                confidence=0.9,
                evidence=[Evidence('shortfall', diff, 'computed')],
                deadline=None,
                action='INVESTIGATE',
                bucket='REVIEW',
                reason="UPI receipt is short and not explained by standard MDR fee"
            ))

    return findings
