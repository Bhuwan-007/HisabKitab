import pandas as pd
from app.rules.base import Finding, Evidence

def run(dataset, matches, cfg) -> list[Finding]:
    findings = []
    
    pb_dict = dataset.purchase_books.set_index('id').to_dict('index')
    g2b_dict = dataset.gstr2b.set_index('id').to_dict('index')
    si_dict = dataset.supplier_invoices.set_index('id').to_dict('index')
    
    # Pre-process rates
    rates = dataset.rates.to_dict('records')
    def get_expected_rate(hsn, dt):
        for r in rates:
            if r['hsn_prefix'] == hsn:
                dt_str = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                if dt_str < str(cfg.GST_RATE_CUTOVER):
                    return float(r['rate_before'])
                return float(r['rate_after'])
        return 18.0

    # Match-based: R-TAX-01
    for m in matches:
        if m.left_type == 'purchase_books' and m.right_type == 'gstr2b':
            pb = pb_dict.get(m.left_id)
            g2b = g2b_dict.get(m.right_id)
            if not pb or not g2b: continue
            
            pb_tax = float(pb['cgst'] + pb['sgst'] + pb['igst'])
            g2b_tax = float(g2b['cgst'] + g2b['sgst'] + g2b['igst'])
            diff = pb_tax - g2b_tax
            
            if abs(diff) > cfg.ROUNDING_TOLERANCE:
                stake = max(0.0, diff)
                reason = "books and GSTR-2B tax mismatch"
                action = 'ASK_CREDIT_NOTE'
                if diff < 0:
                    reason = "supplier reported more than we booked"
                    action = 'CORRECT_BOOKS'
                    
                findings.append(Finding(
                    rule_id='R-TAX-01',
                    issue_type='AMOUNT_MISMATCH',
                    entity_type='purchase_invoice',
                    entity_id=m.left_id,
                    supplier_id=pb['supplier_id'],
                    amount_at_stake=stake,
                    confidence=m.confidence,
                    evidence=[
                        Evidence('books_tax', pb_tax, 'purchase_books'),
                        Evidence('gstr2b_tax', g2b_tax, 'gstr2b_entries')
                    ],
                    deadline=None,
                    action=action,
                    bucket='NEEDS_FIX'
                ))

    # Match books with supplier invoices for R-TAX-02
    si_matches = {}
    for m in matches:
        if m.left_type == 'purchase_books' and m.right_type == 'supplier_invoices':
            si_matches[m.left_id] = m.right_id

    # R-TAX-02 Wrong rate
    for pb_id, pb in pb_dict.items():
        inv_date = pd.to_datetime(pb['invoice_date']).date()
        expected_rate = get_expected_rate(pb['hsn'], inv_date)
        
        si_id = si_matches.get(pb_id)
        charged_rate = None
        if si_id and si_id in si_dict:
            raw = si_dict[si_id].get('rate_pct')
            if pd.notna(raw):
                charged_rate = float(raw)
        
        if charged_rate is None:
            raw = pb.get('rate_pct')
            if pd.notna(raw):
                charged_rate = float(raw)
                
        if charged_rate is None:
            continue
            
        if abs(charged_rate - expected_rate) > 0.01:
            taxable = float(pb['taxable_value'])
            expected_tax = round(taxable * expected_rate / 100, 2)
            charged_tax = round(taxable * charged_rate / 100, 2)
            
            stake = max(0.0, charged_tax - expected_tax)
            bucket = 'NEEDS_FIX'
            action = 'ASK_CREDIT_NOTE'
            reason = "charged wrong tax rate"
            
            if charged_tax < expected_tax:
                stake = 0.0
                bucket = 'REVIEW'
                action = 'INVESTIGATE'
                reason = "charged less than expected; supplier may owe the difference"
            else:
                # check decoy/cutover logic
                # old rate used after cutover?
                # we need to know what the old rate was.
                r_before = None
                for r in rates:
                    if r['hsn_prefix'] == pb['hsn']:
                        r_before = float(r['rate_before'])
                        break
                
                if r_before is not None and abs(charged_rate - r_before) <= 0.01:
                    if inv_date.strftime('%Y-%m-%d') >= str(cfg.GST_RATE_CUTOVER):
                        reason = "old rate used after the 22 Sep 2025 change"
                        
            findings.append(Finding(
                rule_id='R-TAX-02',
                issue_type='WRONG_TAX_RATE',
                entity_type='purchase_invoice',
                entity_id=pb_id,
                supplier_id=pb['supplier_id'],
                amount_at_stake=stake,
                confidence=0.95,
                evidence=[
                    Evidence('invoice_date', inv_date.strftime('%Y-%m-%d'), 'purchase_books'),
                    Evidence('charged_rate', charged_rate, 'supplier_invoices/books'),
                    Evidence('expected_rate', expected_rate, 'rate_table'),
                    Evidence('taxable_value', taxable, 'purchase_books'),
                    Evidence('charged_tax', charged_tax, 'computed'),
                    Evidence('expected_tax', expected_tax, 'computed')
                ],
                deadline=None,
                action=action,
                bucket=bucket,
                reason=reason
            ))

    return findings
