import sqlite3

conn = sqlite3.connect('data/itc_shield.db')
fps = conn.execute("""
    SELECT i.entity_id, pb.invoice_date, s.status_changed_on, s.gstin_status 
    FROM issue i 
    JOIN purchasebook pb ON i.entity_id = pb.id 
    JOIN supplier s ON pb.supplier_id = s.id 
    LEFT JOIN groundtruth g ON g.entity_id = i.entity_id AND g.injected_issue_type='SUPPLIER_GSTIN_CANCELLED'
    WHERE i.issue_type='SUPPLIER_GSTIN_CANCELLED' AND g.id IS NULL
""").fetchall()

print("FPs for SUPPLIER_GSTIN_CANCELLED:")
for r in fps:
    print(r)
