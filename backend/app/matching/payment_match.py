import pandas as pd
from rapidfuzz import fuzz
from datetime import timedelta
from app.config import config
from .invoice_match import MatchRecord
from typing import List

def apply_upi_adjustment(bank_row, sales_row):
    # Hook for stage 3b
    return None

def match_payments(dataset) -> List[MatchRecord]:
    matches = []
    matched_bank = set()
    matched_inv = set()
    
    pb = dataset.purchase_books.merge(dataset.suppliers[['id', 'name']], left_on='supplier_id', right_on='id', suffixes=('', '_sup'))
    pb.rename(columns={'name': 'supplier_name'}, inplace=True)
    pb['total'] = pb['total'].astype(float)
    
    debits = dataset.bank[dataset.bank['direction'] == 'DEBIT']
    
    # a) bank debits to supplier invoices, 1-to-1 by ref or supplier name similarity + amount
    for _, b_row in debits.iterrows():
        if b_row['id'] in matched_bank: continue
        b_amt = float(b_row['amount'])
        c_hint = str(b_row['counterparty_hint']).lower()
        b_ref = str(b_row['reference']).lower()
        b_nar = str(b_row['narration']).lower()
        
        possible_invoices = pb[(pb['total'] == b_amt) & (~pb['id'].isin(matched_inv))]
        best_inv = None
        for _, inv_row in possible_invoices.iterrows():
            inv_raw = str(inv_row['invoice_no_raw']).lower()
            ref_match = (inv_raw in b_nar) or (inv_raw == b_ref)
            name_sim = fuzz.token_sort_ratio(c_hint, str(inv_row['supplier_name']).lower()) / 100.0
            
            if ref_match or name_sim > 0.8:
                best_inv = inv_row
                break
        
        if best_inv is not None:
            matched_bank.add(b_row['id'])
            matched_inv.add(best_inv['id'])
            matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", best_inv['id'], "PAYMENT_EXACT", 1.0, {"amount_diff": 0.0}))

    # b) 1-to-many batch payments
    rem_debits = debits[~debits['id'].isin(matched_bank)]
    for _, b_row in rem_debits.iterrows():
        b_amt = float(b_row['amount'])
        c_hint = str(b_row['counterparty_hint']).lower()
        
        sup_sims = []
        for _, s in dataset.suppliers.iterrows():
            sim = fuzz.token_sort_ratio(c_hint, str(s['name']).lower()) / 100.0
            if sim > 0.8:
                sup_sims.append(s['id'])
                
        for s_id in sup_sims:
            s_invs = pb[(pb['supplier_id'] == s_id) & (~pb['id'].isin(matched_inv))].copy()
            s_invs = s_invs.sort_values('invoice_date')
            found = False
            invs_list = s_invs.to_dict('records')
            
            for i in range(len(invs_list)):
                if found: break
                for j in range(i+1, min(i+15, len(invs_list))):
                    if found: break
                    diff_days = (pd.to_datetime(invs_list[j]['invoice_date']) - pd.to_datetime(invs_list[i]['invoice_date'])).days
                    if diff_days <= 60:
                        total_2 = invs_list[i]['total'] + invs_list[j]['total']
                        if abs(total_2 - b_amt) <= config.ROUNDING_TOLERANCE:
                            matched_bank.add(b_row['id'])
                            matched_inv.add(invs_list[i]['id'])
                            matched_inv.add(invs_list[j]['id'])
                            matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", invs_list[i]['id'], "BATCH_PAYMENT", 0.9, {}))
                            matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", invs_list[j]['id'], "BATCH_PAYMENT", 0.9, {}))
                            found = True
                            break
                        
                        for k in range(j+1, min(j+15, len(invs_list))):
                            diff_days_k = (pd.to_datetime(invs_list[k]['invoice_date']) - pd.to_datetime(invs_list[i]['invoice_date'])).days
                            if diff_days_k <= 60:
                                total_3 = total_2 + invs_list[k]['total']
                                if abs(total_3 - b_amt) <= config.ROUNDING_TOLERANCE:
                                    matched_bank.add(b_row['id'])
                                    matched_inv.add(invs_list[i]['id'])
                                    matched_inv.add(invs_list[j]['id'])
                                    matched_inv.add(invs_list[k]['id'])
                                    matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", invs_list[i]['id'], "BATCH_PAYMENT", 0.9, {}))
                                    matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", invs_list[j]['id'], "BATCH_PAYMENT", 0.9, {}))
                                    matches.append(MatchRecord("bank_transaction", b_row['id'], "purchase_books", invs_list[k]['id'], "BATCH_PAYMENT", 0.9, {}))
                                    found = True
                                    break
            if found:
                break
                
    # c) bank credits to sales invoices by amount
    credits = dataset.bank[dataset.bank['direction'] == 'CREDIT']
    matched_sales = set()
    sales = dataset.sales.copy()
    if not sales.empty:
        sales['total'] = sales['total'].astype(float)
    
    for _, b_row in credits.iterrows():
        b_amt = float(b_row['amount'])
        possible_sales = sales[(abs(sales['total'] - b_amt) <= config.ROUNDING_TOLERANCE) & (~sales['id'].isin(matched_sales))]
        if not possible_sales.empty:
            s_id = possible_sales.iloc[0]['id']
            matched_bank.add(b_row['id'])
            matched_sales.add(s_id)
            matches.append(MatchRecord("bank_transaction", b_row['id'], "sales_invoice", s_id, "RECEIPT_EXACT", 1.0, {"amount_diff": float(possible_sales.iloc[0]['total'] - b_amt)}))
            continue
            
        apply_upi_adjustment(b_row, None)

    return matches
