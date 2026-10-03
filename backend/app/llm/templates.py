def get_fallback_explanation(finding) -> str:
    # Safely extract from evidence
    ev = {e.label: e.value for e in finding.evidence}
    
    t = finding.issue_type
    amt = f"{finding.amount_at_stake:,.2f}"
    
    if t == 'MISSING_IN_GSTR2B':
        # missing invoice {no}
        inv_no = ev.get('invoice_no', 'unknown')
        return f"Supplier has not reported invoice {inv_no} yet, so ₹{amt} of tax credit cannot be claimed. Chase them before the next filing."
    elif t == 'WRONG_TAX_RATE':
        date = ev.get('invoice_date', 'unknown')
        c = ev.get('charged_rate', 0)
        e = ev.get('expected_rate', 0)
        if finding.amount_at_stake == 0:
            return f"This invoice is dated {date}, but charges {c}% instead of {e}%. Supplier charged less than expected; they may owe the difference."
        return f"This invoice is dated {date}, but charges {c}% instead of {e}%. Ask for a credit note for ₹{amt}."
    elif t == 'PAYMENT_180_DAY_RISK':
        days = ev.get('days_left', 0)
        deadline = ev.get('deadline', 'unknown')
        return f"This invoice is unpaid and {days} days remain of the 180-day limit. Pay by {deadline} to keep ₹{amt} of credit."
    elif t == 'UPI_MDR_ADJUSTED':
        fee = ev.get('mdr_fee', 0)
        return f"Deposit is ₹{fee:,.2f} short of the invoice because of the 0.4% UPI merchant fee. This is expected, not an error."
    elif t == 'CIRCULAR_TRADING':
        return "Supplier is part of a loop of invoices between the same firms. This needs a human review, it is not proof of wrongdoing."
    elif t == 'SUPPLIER_GSTIN_CANCELLED':
        return f"The supplier's GSTIN is cancelled, so ₹{amt} of tax credit is at risk. Stop payments immediately."
    elif t == 'AMOUNT_MISMATCH':
        return f"There is a discrepancy in the tax amount between the books and what the supplier filed. The difference is ₹{amt}."
    elif t == 'WRONG_TAX_TYPE':
        return f"The wrong type of tax (IGST vs CGST/SGST) was charged. The amount at stake is ₹{amt}."
    elif t == 'DUPLICATE_INVOICE':
        return f"This looks like a duplicate invoice. We need to remove one to avoid double counting ₹{amt} of tax credit."
    elif t == 'MISSING_IN_BOOKS':
        return "The supplier filed an invoice in GSTR-2B that is missing from our books. We should record it."
    elif t == 'SPLIT_INVOICE':
        return "Multiple invoices were issued just below the approval threshold on the same day. This needs review."
    elif t == 'STATISTICAL_ANOMALY':
        feat = ev.get('top_feature', 'unknown')
        return f"This invoice looks unusual statistically. The main reason flagged is '{feat}'. Needs human review."
    elif t == 'UNMATCHED_PAYMENT':
        return f"A payment of ₹{amt} was made to a supplier but we have no matching invoice for it."
    elif t == 'UNMATCHED_RECEIPT':
        return f"A deposit was received but there is no matching sales invoice for it."
    elif t == 'UPI_SHORT_SETTLEMENT_UNEXPLAINED':
        return f"A UPI deposit was short by ₹{amt} and it is not explained by the standard merchant fee."
    elif t == 'PERIOD_CUTOFF':
        return "There is a timing difference between when the invoice was dated and when it was booked or paid."
    elif t == 'ROUNDING_DIFF':
        return "There is a small rounding difference of ₹1 or less. It has been automatically resolved."
    
    return finding.reason if hasattr(finding, 'reason') and finding.reason else "Manual review needed."
