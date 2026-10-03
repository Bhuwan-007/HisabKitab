import sqlite3
conn = sqlite3.connect('data/itc_shield.db')

# Why is 2003 missing from issues? Check all issues for 2003
iss = conn.execute("SELECT entity_id, issue_type FROM issue WHERE entity_id=2003").fetchall()
print("Issues for 2003:", iss)

# Check what the split detection does for supplier 7 on Sep 12
# All purchase books from supplier 7 in Sep 2026
sup7_sep = conn.execute("SELECT id, invoice_date, taxable_value, invoice_no_raw FROM purchasebook WHERE supplier_id=7 AND invoice_date LIKE '2026-09%' ORDER BY invoice_date, taxable_value").fetchall()
print("\nSupplier 7 Sep 2026 invoices:")
for r in sup7_sep: print(r)

# Check all suppliers for accidental groups
# Supplier that has both 109 and 1002
sup = conn.execute("SELECT id, supplier_id, invoice_date, taxable_value, invoice_no_raw FROM purchasebook WHERE id IN (109, 1002, 519, 387, 165)").fetchall()
print("\nFP invoices:")
for r in sup: print(r)

# Check all issues: did SPLIT_INVOICE for 2003 exist before dedup?
# Let's check what the actual SPLIT analysis produces - look at all findings
# Actually check the issue table for entity 2000-2008:
split_iss = conn.execute("SELECT entity_id, issue_type FROM issue WHERE entity_id BETWEEN 2000 AND 2008").fetchall()
print("\nIssues for 2000-2008:", split_iss)

# Also understand: the sliding window on Sep 12 for supplier 7
# has 2003 (38862), 2004 (48831), 2005 (49247)
# All pass 70% threshold (35000). Sum > 50000. 
# Current group [0] = 2003, finding entity_id = 2003
# But above shows entity_id=2004...
# Let me check if 2003 was deduped
pre_iss = conn.execute("SELECT entity_id, issue_type FROM issue WHERE entity_id=2003 OR entity_id=2004 OR entity_id=2005").fetchall()
print("\nIssues for 2003-2005:", pre_iss)

# Also check: what comes before 2003 in supplier 7's sorted candidates?
# Is there any invoice from supplier 7 that is >= 35000 on or near Sep 12?
sup7_candidates = conn.execute("""
    SELECT id, invoice_date, taxable_value FROM purchasebook 
    WHERE supplier_id=7 AND taxable_value < 50000 AND taxable_value >= 35000
    ORDER BY invoice_date
""").fetchall()
print("\nSupplier 7 split candidates (35k-50k):")
for r in sup7_candidates: print(r)
