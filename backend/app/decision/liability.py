from app.schemas import LiabilityResponse
import pandas as pd

def compute_liability(dataset, issues, period: str) -> LiabilityResponse:
    # 1. total_itc_booked
    pb = dataset.purchase_books
    pb_period = pb[pb['itc_period'] == period]
    
    # duplicates counted once? 
    # If a duplicate is in purchase_books, it is flagged by R-DUP-01.
    # The rule says "duplicates counted once". If there are duplicates, 
    # we should ideally count only unique invoice_no_norm per supplier?
    # Actually, R-DUP-01 flags the EXTRAS, keeping the earliest as original.
    # So if we just sum all purchase_books in the period and then the issue amount_at_stake for DUPLICATE_INVOICE takes care of reducing it?
    # Wait, "total_itc_booked = sum(cgst+sgst+igst) over purchase_books in period, duplicates counted once"
    # To count duplicates once, we can group by (supplier_id, invoice_no_norm) and take the first?
    # Or maybe the dataset has `is_dup`? Let's just group by supplier_id and invoice_no_norm.
    pb_unique = pb_period.drop_duplicates(subset=['supplier_id', 'invoice_no_norm'])
    
    total_itc_booked = pb_unique['cgst'].sum() + pb_unique['sgst'].sum() + pb_unique['igst'].sum()
    
    # 2. at_risk
    # sum over invoices of max(amount_at_stake of AT_RISK issues)
    # 3. needs_fix
    # sum over invoices NOT already in at_risk of max(amount_at_stake of NEEDS_FIX issues)
    
    at_risk_map = {}
    needs_fix_map = {}
    
    for issue in issues:
        if issue.bucket == 'AT_RISK':
            if issue.entity_type == 'purchase_invoice':
                at_risk_map[issue.entity_id] = max(at_risk_map.get(issue.entity_id, 0), issue.amount_at_stake)
            elif issue.issue_type == 'MISSING_IN_GSTR2B':
                # MISSING_IN_GSTR2B is AT_RISK, entity is purchase_invoice
                at_risk_map[issue.entity_id] = max(at_risk_map.get(issue.entity_id, 0), issue.amount_at_stake)
            elif issue.issue_type == 'SUPPLIER_GSTIN_CANCELLED':
                # entity is supplier, but we need to sum over invoices!
                # Ah! "sum over invoices of max(amount_at_stake)".
                # But wait, my implementation of SUPPLIER_GSTIN_CANCELLED outputs entity_type='supplier', but amount_at_stake = 0?
                # No, SUPPLIER_GSTIN_CANCELLED outputs finding per invoice!
                # Wait, does it? Let me check missing.py
                at_risk_map[issue.entity_id] = max(at_risk_map.get(issue.entity_id, 0), issue.amount_at_stake)
                
        elif issue.bucket == 'NEEDS_FIX':
            if issue.entity_type == 'purchase_invoice':
                needs_fix_map[issue.entity_id] = max(needs_fix_map.get(issue.entity_id, 0), issue.amount_at_stake)
            elif issue.issue_type == 'MISSING_IN_BOOKS':
                # entity is gstr2b_entry.
                needs_fix_map[f"gstr2b_{issue.entity_id}"] = max(needs_fix_map.get(f"gstr2b_{issue.entity_id}", 0), issue.amount_at_stake)

    at_risk = sum(at_risk_map.values())
    
    needs_fix = 0.0
    for eid, amt in needs_fix_map.items():
        if eid not in at_risk_map:
            needs_fix += amt
            
    safe_to_claim = max(0.0, total_itc_booked - at_risk - needs_fix)
    
    # Liability estimate
    sales = dataset.sales
    sales_period = sales[sales['invoice_date'].str.startswith(period)] # simple way to match YYYY-MM
    output_tax = sales_period['cgst'].sum() + sales_period['sgst'].sum() + sales_period['igst'].sum()
    
    itc_claim_now = safe_to_claim
    itc_if_all_recovered = safe_to_claim + at_risk + needs_fix
    
    net_payable_now = max(0.0, output_tax - itc_claim_now)
    net_payable_if_recovered = max(0.0, output_tax - itc_if_all_recovered)
    cash_impact_of_issues = net_payable_now - net_payable_if_recovered
    
    return {
        "total_itc_booked": round(total_itc_booked, 2),
        "at_risk": round(at_risk, 2),
        "needs_fix": round(needs_fix, 2),
        "safe_to_claim": round(safe_to_claim, 2),
        "liability": LiabilityResponse(
            output_tax=round(output_tax, 2),
            itc_claim_now=round(itc_claim_now, 2),
            itc_if_all_recovered=round(itc_if_all_recovered, 2),
            net_payable_now=round(net_payable_now, 2),
            net_payable_if_recovered=round(net_payable_if_recovered, 2),
            cash_impact_of_issues=round(cash_impact_of_issues, 2)
        )
    }
