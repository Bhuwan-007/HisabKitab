def get_bucket(issue_type: str) -> str:
    buckets = {
        'MISSING_IN_GSTR2B': 'AT_RISK',
        'SUPPLIER_GSTIN_CANCELLED': 'AT_RISK',
        'PAYMENT_180_DAY_RISK': 'AT_RISK',
        
        'AMOUNT_MISMATCH': 'NEEDS_FIX',
        'WRONG_TAX_RATE': 'NEEDS_FIX',
        'WRONG_TAX_TYPE': 'NEEDS_FIX',
        'DUPLICATE_INVOICE': 'NEEDS_FIX',
        'MISSING_IN_BOOKS': 'NEEDS_FIX',
        
        'SPLIT_INVOICE': 'REVIEW',
        'CIRCULAR_TRADING': 'REVIEW',
        'STATISTICAL_ANOMALY': 'REVIEW',
        'UNMATCHED_PAYMENT': 'REVIEW',
        'UNMATCHED_RECEIPT': 'REVIEW',
        'UPI_SHORT_SETTLEMENT_UNEXPLAINED': 'REVIEW',
        'PERIOD_CUTOFF': 'REVIEW',
        
        'ROUNDING_DIFF': 'AUTO_RESOLVED',
        'UPI_MDR_ADJUSTED': 'AUTO_RESOLVED'
    }
    return buckets.get(issue_type, 'REVIEW')

def calculate_priority_severity(issue_type: str, amount_at_stake: float, confidence: float, days_left: int | float | None):
    # Urgency multiplier
    if days_left is not None:
        if days_left <= 7:
            urgency_multiplier = 1.5
        elif days_left <= 15:
            urgency_multiplier = 1.25
        else:
            urgency_multiplier = 1.0
    else:
        urgency_multiplier = 1.0
        
    priority_score = amount_at_stake * urgency_multiplier * confidence
    
    bucket = get_bucket(issue_type)
    if bucket == 'REVIEW' and amount_at_stake == 0:
        priority_score = 1000 * confidence
        
    # Severity
    if issue_type == 'SUPPLIER_GSTIN_CANCELLED' or priority_score >= 100000:
        severity = 'CRITICAL'
    elif priority_score >= 25000:
        severity = 'HIGH'
    elif priority_score >= 5000:
        severity = 'MEDIUM'
    else:
        severity = 'LOW'
        
    return {
        "priority_score": round(priority_score, 2),
        "severity": severity,
        "bucket": bucket
    }
