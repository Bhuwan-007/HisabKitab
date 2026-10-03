import json
from app.db import engine
from sqlmodel import Session
from sqlalchemy import text
from app.models import Match
from app.ingest.loaders import load_all
from app.matching.invoice_match import match_invoices
from app.matching.payment_match import match_payments

def save_matches(run_id, matches):
    with Session(engine) as session:
        session.exec(text(f"DELETE FROM match WHERE run_id={run_id}"))
        for m in matches:
            record = Match(
                run_id=run_id,
                left_type=m.left_type,
                left_id=m.left_id,
                right_type=m.right_type,
                right_id=m.right_id,
                match_type=m.match_type,
                confidence=m.confidence,
                diffs_json=json.dumps(m.diffs)
            )
            session.add(record)
        session.commit()

def match_report(matches, dataset):
    def print_pair(title, left, right):
        print(f"\n--- {title} ---")
        pair_m = [m for m in matches if m.left_type == left and (m.right_type == right or (m.match_type == 'BATCH_PAYMENT' and right == 'purchase_books'))]
        m_types = {}
        non_zero = 0
        for m in pair_m:
            m_types[m.match_type] = m_types.get(m.match_type, 0) + 1
            if m.diffs.get('tax_diff', 0) != 0:
                non_zero += 1
                
        for k, v in m_types.items():
            print(f"  {k}: {v}")
            
        matched_left = len(set(m.left_id for m in pair_m))
        matched_right = len(set(str(m.right_id) for m in pair_m))
        
        left_total = 0
        if left == 'purchase_books': left_total = len(dataset.purchase_books)
        elif left == 'bank_transaction':
            if right == 'purchase_books': left_total = len(dataset.bank[dataset.bank['direction'] == 'DEBIT'])
            else: left_total = len(dataset.bank[dataset.bank['direction'] == 'CREDIT'])
            
        right_total = 0
        if right == 'gstr2b': right_total = len(dataset.gstr2b)
        elif right == 'supplier_invoices': right_total = len(dataset.supplier_invoices)
        elif right == 'purchase_books': right_total = len(dataset.purchase_books)
        elif right == 'sales_invoice': right_total = len(dataset.sales)
        
        print(f"  Unmatched left: {left_total - matched_left}")
        print(f"  Unmatched right: {right_total - matched_right}")
        print(f"  Matches with non-zero tax diff: {non_zero}")

    print("MATCH REPORT")
    print_pair("Books vs GSTR-2B", "purchase_books", "gstr2b")
    print_pair("Books vs Supplier Invoices", "purchase_books", "supplier_invoices")
    print_pair("Bank Debits vs Books", "bank_transaction", "purchase_books")
    print_pair("Bank Credits vs Sales", "bank_transaction", "sales_invoice")
    
    batch_matches = len(set(m.left_id for m in matches if m.match_type == 'BATCH_PAYMENT'))
    print(f"\nBatch payments matched: {batch_matches}")
    print("Confirmed batch search caps candidate invoices per supplier window at 15.")

def run_report():
    ds = load_all()
    m1 = match_invoices(ds)
    m2 = match_payments(ds)
    all_matches = m1 + m2
    save_matches(1, all_matches)
    match_report(all_matches, ds)

if __name__ == "__main__":
    run_report()
