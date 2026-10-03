import sqlite3

c = sqlite3.connect("data/itc_shield.db")
tabs = [r[0] for r in c.execute("select name from sqlite_master where type='table' order by 1")]

def count(t):
    return c.execute('select count(*) from "%s"' % t).fetchone()[0]

print("TABLE ROW COUNTS")
for t in tabs:
    print("  %-22s %d" % (t, count(t)))

gt = next((t for t in tabs if "truth" in t.lower()), None)
print("\nGROUND TRUTH BY TYPE (table: %s)" % gt)
for row in c.execute('select injected_issue_type, count(*) from "%s" group by 1 order by 2 desc' % gt):
    print("  ", row)

print("\nSPLIT INVOICE ROWS (must have DIFFERENT invoice numbers and amounts)")
pb = next((t for t in tabs if "purchase" in t.lower()), None)
try:
    ids = c.execute('select entity_id from "%s" where injected_issue_type=?' % gt, ("SPLIT_INVOICE",)).fetchall()
    for (eid,) in ids:
        print("  ", c.execute(
            'select id, supplier_id, invoice_no_raw, invoice_date, taxable_value, total from "%s" where id=?' % pb,
            (eid,)).fetchone())
except Exception as e:
    print("  could not read split rows:", e)