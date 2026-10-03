import pandas as pd
from rapidfuzz import fuzz
from dataclasses import dataclass
from typing import Dict, Any, List
from app.config import config

@dataclass
class MatchRecord:
    left_type: str
    left_id: int
    right_type: str
    right_id: int
    match_type: str
    confidence: float
    diffs: Dict[str, Any]

def match_invoices_pair(left_df: pd.DataFrame, right_df: pd.DataFrame, left_type: str, right_type: str) -> List[MatchRecord]:
    matches = []
    matched_left = set()
    matched_right = set()

    if left_df.empty or right_df.empty:
        return matches

    left_df['total_tax'] = left_df['cgst'] + left_df['sgst'] + left_df['igst']
    right_df['total_tax'] = right_df['cgst'] + right_df['sgst'] + right_df['igst']

    left_grouped = left_df.groupby('supplier_gstin')
    right_grouped = right_df.groupby('supplier_gstin')
    
    common_gstins = set(left_grouped.groups.keys()).intersection(set(right_grouped.groups.keys()))
    
    for gstin in common_gstins:
        l_group = left_grouped.get_group(gstin)
        r_group = right_grouped.get_group(gstin)
        
        # EXACT PASS
        exact = l_group.merge(r_group, on='invoice_no_norm', suffixes=('_l', '_r'))
        exact['date_diff'] = (pd.to_datetime(exact['invoice_date_l']) - pd.to_datetime(exact['invoice_date_r'])).dt.days.abs()
        exact = exact.sort_values('date_diff')
        
        for _, row in exact.iterrows():
            l_id, r_id = row['id_l'], row['id_r']
            if l_id in matched_left or r_id in matched_right:
                continue
            matched_left.add(l_id)
            matched_right.add(r_id)
            diffs = {
                "taxable_diff": float(row['taxable_value_l'] - row['taxable_value_r']),
                "tax_diff": float(row['total_tax_l'] - row['total_tax_r']),
                "date_diff_days": int((pd.to_datetime(row['invoice_date_l']) - pd.to_datetime(row['invoice_date_r'])).days),
                "invoice_no_similarity": 1.0
            }
            matches.append(MatchRecord(left_type, l_id, right_type, r_id, "EXACT", 1.0, diffs))

        # FUZZY PASS
        l_rem = l_group[~l_group['id'].isin(matched_left)]
        r_rem = r_group[~r_group['id'].isin(matched_right)]
        for _, lr in l_rem.iterrows():
            best_r = None
            best_sim = 0
            best_diffs = None
            for _, rr in r_rem.iterrows():
                if rr['id'] in matched_right:
                    continue
                tax_diff = abs(lr['total_tax'] - rr['total_tax'])
                if tax_diff <= config.ROUNDING_TOLERANCE:
                    sim = fuzz.ratio(lr['invoice_no_norm'], rr['invoice_no_norm']) / 100.0
                    if sim > 0.85 and sim > best_sim:
                        best_sim = sim
                        best_r = rr
                        best_diffs = {
                            "taxable_diff": float(lr['taxable_value'] - rr['taxable_value']),
                            "tax_diff": float(lr['total_tax'] - rr['total_tax']),
                            "date_diff_days": int((pd.to_datetime(lr['invoice_date']) - pd.to_datetime(rr['invoice_date'])).days),
                            "invoice_no_similarity": sim
                        }
            if best_r is not None:
                matched_left.add(lr['id'])
                matched_right.add(best_r['id'])
                conf = min(0.95, round(best_sim, 2))
                matches.append(MatchRecord(left_type, lr['id'], right_type, best_r['id'], "FUZZY", conf, best_diffs))
                
        # AMOUNT PASS
        l_rem = l_group[~l_group['id'].isin(matched_left)]
        r_rem = r_group[~r_group['id'].isin(matched_right)]
        for _, lr in l_rem.iterrows():
            best_r = None
            best_diffs = None
            for _, rr in r_rem.iterrows():
                if rr['id'] in matched_right:
                    continue
                tax_diff = abs(lr['total_tax'] - rr['total_tax'])
                if tax_diff == 0:
                    date_diff = abs((pd.to_datetime(lr['invoice_date']) - pd.to_datetime(rr['invoice_date'])).days)
                    if date_diff <= 10:
                        best_r = rr
                        best_diffs = {
                            "taxable_diff": float(lr['taxable_value'] - rr['taxable_value']),
                            "tax_diff": 0.0,
                            "date_diff_days": int((pd.to_datetime(lr['invoice_date']) - pd.to_datetime(rr['invoice_date'])).days),
                            "invoice_no_similarity": round(fuzz.ratio(lr['invoice_no_norm'], rr['invoice_no_norm']) / 100.0, 2)
                        }
                        break 
            if best_r is not None:
                matched_left.add(lr['id'])
                matched_right.add(best_r['id'])
                matches.append(MatchRecord(left_type, lr['id'], right_type, best_r['id'], "AMOUNT", 0.55, best_diffs))
                
    return matches

def match_invoices(dataset) -> List[MatchRecord]:
    pb = dataset.purchase_books.merge(dataset.suppliers[['id', 'gstin']], left_on='supplier_id', right_on='id', suffixes=('', '_sup'))
    pb.rename(columns={'gstin': 'supplier_gstin'}, inplace=True)
    
    m1 = match_invoices_pair(pb, dataset.gstr2b, "purchase_books", "gstr2b")
    m2 = match_invoices_pair(pb, dataset.supplier_invoices, "purchase_books", "supplier_invoices")
    return m1 + m2
