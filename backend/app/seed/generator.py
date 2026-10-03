import random
import csv
import json
import os
from datetime import date, timedelta
from app.config import config
from app.models import (
    Business, Supplier, Customer, PurchaseBook, SupplierInvoice, GSTR2BEntry,
    SalesInvoice, BankTransaction, TradeLink, RateTable, GroundTruth
)
from app.db import engine, init_db
from sqlmodel import Session, select
from app.ingest.normalize import normalize_invoice_no, round_rupees

def get_rate(rates, hsn, dt):
    for r in rates:
        if r.hsn_prefix == hsn:
            return r.rate_before if dt < date(2025, 9, 22) else r.rate_after
    return 18.0

def calc_tax(val, rate, sup_state):
    tax = round_rupees(val * rate / 100.0)
    if sup_state == "07":
        return round_rupees(tax/2), round_rupees(tax/2), 0.0, tax
    return 0.0, 0.0, tax, tax

def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_data():
    random.seed(config.RANDOM_SEED)
    init_db()
    with Session(engine) as session:
        from sqlalchemy import text
        # Clear tables
        for model in [PurchaseBook, SupplierInvoice, GSTR2BEntry, SalesInvoice, BankTransaction, TradeLink, GroundTruth, Supplier, Customer, RateTable, Business]:
            session.exec(text(f"DELETE FROM {model.__tablename__}"))
            
        business = Business(id=1, name="Meridian Components Pvt Ltd", gstin="07ZZZZZ9999Z1Z1", state_code="07")
        session.add(business)
        
        rates = []
        with open("app/seed/rate_table.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rt = RateTable(
                    hsn_prefix=row["hsn_prefix"], description=row["description"],
                    rate_before=float(row["rate_before"]), rate_after=float(row["rate_after"])
                )
                rates.append(rt)
                session.add(rt)
                
        states = ["07"] * 16 + ["06", "27", "29", "33", "09"] * 5
        suppliers = []
        for i in range(1, 41):
            st = states[i-1]
            sup = Supplier(
                id=i, gstin=f"{st}ZZZZZ{9000+i}Z1Z1", name=f"Supplier {i}", state_code=st,
                gstin_status="ACTIVE", avg_filing_delay_days=random.randint(0, 5),
                filings_last_6m_on_time=random.randint(4, 6), is_shell_flag=False
            )
            suppliers.append(sup)
        
        # 4 chronic late filers
        for i in range(2, 6):
            suppliers[i].avg_filing_delay_days = 40
            suppliers[i].filings_last_6m_on_time = 0
            
        # Ghost
        suppliers[0].gstin_status = "CANCELLED"
        suppliers[0].status_changed_on = date(2025, 12, 1)
        suppliers[1].gstin_status = "CANCELLED"
        suppliers[1].status_changed_on = date(2026, 2, 1)
        
        for sup in suppliers:
            session.add(sup)
            
        customers = []
        for i in range(1, 26):
            c = Customer(id=i, name=f"Customer {i}", state_code="07", gstin=f"07ZZZZZ8000C{i:02d}")
            customers.append(c)
            session.add(c)
            
        start_date = date(2025, 7, 1)
        end_date = date(2026, 10, 15)
        
        hsn_list = [r.hsn_prefix for r in rates]
        
        # Generate 520 clean base purchases
        purchases = []
        for i in range(1, 521):
            dt = rand_date(start_date, end_date)
            # Denser in last 3 months
            if random.random() < 0.4:
                dt = rand_date(date(2026, 7, 15), end_date)
            sup = random.choice(suppliers)
            hsn = random.choice(hsn_list)
            val = round_rupees(random.uniform(5000, 150000))
            
            raw_no = f"INV/{i}"
            if random.random() < 0.2:
                raw_no = random.choice([f"INV/25-26/{i}", f"BILL-{i}", str(i)])
                
            norm_no = normalize_invoice_no(raw_no)
            rate = get_rate(rates, hsn, dt)
            c, s, ig, t = calc_tax(val, rate, sup.state_code)
            
            p = {
                "id": i, "supplier_id": sup.id, "sup_gstin": sup.gstin, "sup_state": sup.state_code,
                "invoice_no_raw": raw_no, "invoice_no_norm": norm_no, "invoice_date": dt,
                "hsn": hsn, "val": val, "rate": rate, "c": c, "s": s, "ig": ig, "t": t
            }
            purchases.append(p)

        # Injections
        gt = []
        def add_gt(etype, eid, itype):
            gt.append(GroundTruth(entity_type=etype, entity_id=eid, injected_issue_type=itype, note=""))

        # Missing in 2B (14) - from the 4 late filers
        missing_2b = random.sample([p for p in purchases if p["supplier_id"] in [3, 4, 5, 6]], 14)
        for m in missing_2b:
            m["miss_2b"] = True
            add_gt("purchase_invoice", m["id"], "MISSING_IN_GSTR2B")

        # Ghost (6) - assigned to cancelled suppliers, date after cancellation
        ghost = random.sample([p for p in purchases if p["supplier_id"] in [1, 2] and not p.get("miss_2b")], 6)
        for g in ghost:
            sup = suppliers[g["supplier_id"]-1]
            g["invoice_date"] = rand_date(sup.status_changed_on, end_date)
            rate = get_rate(rates, g["hsn"], g["invoice_date"])
            c, s, ig, t = calc_tax(g["val"], rate, sup.state_code)
            g["rate"] = rate; g["c"] = c; g["s"] = s; g["ig"] = ig; g["t"] = t
            g["miss_2b"] = True
            add_gt("purchase_invoice", g["id"], "SUPPLIER_GSTIN_CANCELLED")

        # Amount mismatch (10)
        amt_mismatch = random.sample([p for p in purchases if not p.get("miss_2b")], 10)
        for a in amt_mismatch:
            a["gstr2b_tax_diff"] = random.choice([0.9, 1.1])
            add_gt("purchase_invoice", a["id"], "AMOUNT_MISMATCH")

        # Duplicates (8)
        dups = random.sample([p for p in purchases if not p.get("miss_2b") and "gstr2b_tax_diff" not in p], 8)
        extra_dups = []
        dup_id = 1000
        for i, d in enumerate(dups):
            nd = d.copy()
            nd["id"] = dup_id
            nd["is_dup"] = True
            if i < 3: # fuzzy
                if i == 0:
                    nd["invoice_no_raw"] = d["invoice_no_raw"].replace("/", "-") + "A"
                elif i == 1:
                    nd["invoice_no_raw"] = "REV-" + d["invoice_no_raw"]
                else:
                    nd["invoice_no_raw"] = d["invoice_no_raw"] + "/DUPL"
                nd["invoice_no_norm"] = normalize_invoice_no(nd["invoice_no_raw"])
                nd["invoice_date"] = d["invoice_date"] + timedelta(days=random.choice([1, -1, 2]))
            extra_dups.append(nd)
            add_gt("purchase_invoice", dup_id, "DUPLICATE_INVOICE")
            dup_id += 1
        purchases.extend(extra_dups)

        # Wrong rate (10)
        wrong_rate = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup") and "gstr2b_tax_diff" not in p], 10)
        stale_hsns = ["4819", "6307", "8483", "8708"]
        for i, w in enumerate(wrong_rate):
            if i < 6:
                w["hsn"] = random.choice(stale_hsns)
                w["invoice_date"] = rand_date(date(2025, 9, 23), end_date)
                expected_rate = get_rate(rates, w["hsn"], w["invoice_date"])
                w["wrong_rate"] = 12.0 if w["hsn"] in ["4819", "6307"] else 28.0
            else:
                w["wrong_rate"] = 0.0
            add_gt("purchase_invoice", w["id"], "WRONG_TAX_RATE")

        # Decoys (8) - correct old rate before cutover
        decoys = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup") and "gstr2b_tax_diff" not in p and "wrong_rate" not in p], 8)
        for d in decoys:
            d["hsn"] = random.choice(stale_hsns)
            d["invoice_date"] = rand_date(date(2025, 9, 15), date(2025, 9, 21))
            rate = get_rate(rates, d["hsn"], d["invoice_date"])
            c, s, ig, t = calc_tax(d["val"], rate, d["sup_state"])
            d["rate"] = rate; d["c"] = c; d["s"] = s; d["ig"] = ig; d["t"] = t
            add_gt("purchase_invoice", d["id"], None)

        # Wrong tax type (4)
        wrong_type = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup") and "gstr2b_tax_diff" not in p and "wrong_rate" not in p], 4)
        for w in wrong_type:
            w["wrong_type"] = True
            add_gt("purchase_invoice", w["id"], "WRONG_TAX_TYPE")

        # Rounding (15)
        rounding = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup") and "gstr2b_tax_diff" not in p and "wrong_rate" not in p and "wrong_type" not in p], 15)
        for r in rounding:
            r["rounding_diff"] = round(random.uniform(-0.99, 0.99), 2)
            add_gt("purchase_invoice", r["id"], "ROUNDING_DIFF")

        # Period cutoff (6)
        cutoff = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup") and "gstr2b_tax_diff" not in p and "wrong_rate" not in p], 6)
        for c in cutoff:
            c["invoice_date"] = date(2026, 8, 30)
            c["period_cutoff"] = True
            add_gt("purchase_invoice", c["id"], "PERIOD_CUTOFF")

        # 180-day risk (8)
        unpaid = random.sample([p for p in purchases if not p.get("is_dup")], 8)
        for u in unpaid:
            u["invoice_date"] = rand_date(date(2026, 4, 1), date(2026, 5, 20)) # 150 to 200 days before 2026-10-18
            u["unpaid"] = True
            rate = get_rate(rates, u["hsn"], u["invoice_date"])
            c, s, ig, t = calc_tax(u["val"], rate, u["sup_state"])
            u["rate"] = rate; u["c"] = c; u["s"] = s; u["ig"] = ig; u["t"] = t
            add_gt("purchase_invoice", u["id"], "PAYMENT_180_DAY_RISK")

        # Split invoices (3 groups x 3)
        split_src = random.sample([p for p in purchases if not p.get("is_dup")], 3)
        split_id = 2000
        for s_src in split_src:
            for j in range(3):
                ns = s_src.copy()
                ns["id"] = split_id
                ns["val"] = round_rupees(random.uniform(38000, 49500))
                rate = get_rate(rates, ns["hsn"], ns["invoice_date"])
                c, s, ig, t = calc_tax(ns["val"], rate, ns["sup_state"])
                ns["rate"] = rate; ns["c"] = c; ns["s"] = s; ns["ig"] = ig; ns["t"] = t
                ns["invoice_no_raw"] = s_src["invoice_no_raw"] + f"-{j}"
                ns["invoice_no_norm"] = normalize_invoice_no(ns["invoice_no_raw"])
                ns["is_split"] = True
                add_gt("purchase_invoice", split_id, "SPLIT_INVOICE")
                purchases.append(ns)
                split_id += 1

        # Missing in books (6) - exist in 2B, not in purchases
        missing_books = []
        for i in range(6):
            mid = 3000 + i
            missing_books.append({
                "id": mid, "supplier_id": 10, "sup_gstin": suppliers[9].gstin,
                "invoice_no_raw": f"MB-{i}", "invoice_no_norm": f"MB{i}",
                "invoice_date": date(2026, 9, 10), "val": 10000.0, "c": 900.0, "s": 900.0, "ig": 0.0
            })
            add_gt("gstr2b_entry", mid, "MISSING_IN_BOOKS")
            
        # Statistical anomalies (6)
        anomalies = random.sample([p for p in purchases if not p.get("miss_2b") and not p.get("is_dup")], 6)
        for a in anomalies:
            a["val"] = round_rupees(random.uniform(800000, 950000)) # extreme
            rate = get_rate(rates, a["hsn"], a["invoice_date"])
            c, s, ig, t = calc_tax(a["val"], rate, a["sup_state"])
            a["rate"] = rate; a["c"] = c; a["s"] = s; a["ig"] = ig; a["t"] = t
            add_gt("purchase_invoice", a["id"], "STATISTICAL_ANOMALY")

        # Write to DB
        for p in purchases:
            # books
            rate = p.get("wrong_rate", p["rate"])
            c = p["c"]
            s = p["s"]
            ig = p["ig"]
            if p.get("wrong_type"):
                c, s, ig = (0.0, 0.0, p["t"]) if p["sup_state"] == "07" else (p["t"]/2, p["t"]/2, 0.0)
            
            pb = PurchaseBook(
                id=p["id"], supplier_id=p["supplier_id"], invoice_no_raw=p["invoice_no_raw"],
                invoice_no_norm=p["invoice_no_norm"], invoice_date=p["invoice_date"],
                booked_on=p["invoice_date"] + timedelta(days=2),
                itc_period=p["invoice_date"].strftime("%Y-%m") if not p.get("period_cutoff") else (p["invoice_date"] + timedelta(days=10)).strftime("%Y-%m"),
                hsn=p["hsn"], taxable_value=p["val"], rate_pct=rate,
                cgst=c, sgst=s, igst=ig, total=round_rupees(p["val"] + p["t"]), place_of_supply_state="07"
            )
            session.add(pb)
            
            # invoice document
            inv_rate = rate
            inv_c, inv_s, inv_ig = c, s, ig
            si = SupplierInvoice(
                id=p["id"], supplier_gstin=p["sup_gstin"], invoice_no_raw=p["invoice_no_raw"],
                invoice_no_norm=p["invoice_no_norm"], invoice_date=p["invoice_date"],
                hsn=p["hsn"], taxable_value=p["val"], rate_pct=inv_rate,
                cgst=inv_c, sgst=inv_s, igst=inv_ig, total=pb.total
            )
            session.add(si)
            
            # gstr2b
            if not p.get("miss_2b"):
                # if amount mismatch, gstr2b diff
                diff = p.get("gstr2b_tax_diff", 1.0)
                g2b_c = round_rupees(c * diff)
                g2b_s = round_rupees(s * diff)
                g2b_ig = round_rupees(ig * diff)
                
                # rounding diff
                if p.get("rounding_diff"):
                    g2b_c += p["rounding_diff"]/2 if g2b_c else 0
                    g2b_s += p["rounding_diff"]/2 if g2b_s else 0
                    g2b_ig += p["rounding_diff"] if g2b_ig else 0

                g2b = GSTR2BEntry(
                    id=p["id"], supplier_gstin=p["sup_gstin"], invoice_no_raw=p["invoice_no_raw"],
                    invoice_no_norm=p["invoice_no_norm"], invoice_date=p["invoice_date"],
                    taxable_value=p["val"], cgst=g2b_c, sgst=g2b_s, igst=g2b_ig,
                    return_period=p["invoice_date"].strftime("%Y-%m"),
                    filed_on=p["invoice_date"] + timedelta(days=12)
                )
                session.add(g2b)
                
        for mb in missing_books:
            g2b = GSTR2BEntry(
                id=mb["id"], supplier_gstin=mb["sup_gstin"], invoice_no_raw=mb["invoice_no_raw"],
                invoice_no_norm=mb["invoice_no_norm"], invoice_date=mb["invoice_date"],
                taxable_value=mb["val"], cgst=mb["c"], sgst=mb["s"], igst=mb["ig"],
                return_period="2026-09", filed_on=date(2026, 10, 12)
            )
            session.add(g2b)

        # Sales invoices (420)
        sales = []
        for i in range(1, 421):
            dt = rand_date(start_date, end_date)
            val = round_rupees(random.uniform(1000, 50000))
            if i <= 40:
                val = round_rupees(random.uniform(2500, 5000))
                dt = rand_date(date(2026, 10, 15), end_date) # UPI >= 2000
            
            c, s, ig, t = calc_tax(val, 18.0, "07")
            si = SalesInvoice(
                id=i, customer_id=random.randint(1, 25), invoice_no=f"SAL/{i}",
                invoice_date=dt, hsn="9983", taxable_value=val, rate_pct=18.0,
                cgst=c, sgst=s, igst=ig, total=round_rupees(val+t)
            )
            sales.append(si)
            session.add(si)

        # Bank TXNs (~900)
        txn_id = 1
        for p in purchases:
            if not p.get("unpaid"):
                bt = BankTransaction(
                    id=txn_id, txn_date=p["invoice_date"] + timedelta(days=10),
                    direction="DEBIT", amount=round_rupees(p["val"] + p["t"]),
                    channel="NEFT", narration=f"Paid {p['invoice_no_raw']}",
                    counterparty_hint=suppliers[p["supplier_id"]-1].name,
                    reference=f"REF{txn_id}"
                )
                session.add(bt)
                txn_id += 1
                
        # Unmatched payment (5)
        for i in range(5):
            bt = BankTransaction(
                id=txn_id, txn_date=date(2026, 9, 20), direction="DEBIT", amount=5000.0,
                channel="NEFT", narration="Advance", counterparty_hint="Supplier 10", reference=f"REF{txn_id}"
            )
            session.add(bt)
            add_gt("bank_transaction", txn_id, "UNMATCHED_PAYMENT")
            txn_id += 1
            
        # Sales payments
        # UPI MDR receipts: 20
        # UPI decoys: 8
        # UPI unexplained short: 3
        # Unmatched receipts: 4
        
        for i, s in enumerate(sales):
            if i < 20: # MDR receipts
                mdr = min(round(s.total * 0.004, 2), 300.0)
                if i == 0:
                    s.total = 80000.0 # Force cap
                    mdr = 300.0
                bt = BankTransaction(
                    id=txn_id, txn_date=s.invoice_date, direction="CREDIT",
                    amount=round_rupees(s.total - mdr), channel="UPI", narration="UPI SETTLE",
                    counterparty_hint="UPI", reference=f"REF{txn_id}", txn_kind="P2M"
                )
                add_gt("bank_transaction", txn_id, "UPI_MDR_ADJUSTED")
            elif i < 28: # Decoys (before effective or <= 2000)
                if i < 24:
                    s.invoice_date = date(2026, 10, 10) # Before 15th
                else:
                    s.total = 1500.0
                bt = BankTransaction(
                    id=txn_id, txn_date=s.invoice_date, direction="CREDIT",
                    amount=s.total, channel="UPI", narration="UPI",
                    counterparty_hint="UPI", reference=f"REF{txn_id}", txn_kind="P2M"
                )
                add_gt("bank_transaction", txn_id, None)
            elif i < 31: # Unexplained short
                bt = BankTransaction(
                    id=txn_id, txn_date=s.invoice_date, direction="CREDIT",
                    amount=round_rupees(s.total - 150.0), channel="UPI", narration="UPI",
                    counterparty_hint="UPI", reference=f"REF{txn_id}", txn_kind="P2M"
                )
                add_gt("bank_transaction", txn_id, "UPI_SHORT_SETTLEMENT_UNEXPLAINED")
            else:
                bt = BankTransaction(
                    id=txn_id, txn_date=s.invoice_date, direction="CREDIT",
                    amount=s.total, channel="NEFT", narration="Payment",
                    counterparty_hint="Cust", reference=f"REF{txn_id}"
                )
            session.add(bt)
            txn_id += 1
            
        # Unmatched receipts
        for i in range(4):
            bt = BankTransaction(
                id=txn_id, txn_date=date(2026, 9, 20), direction="CREDIT", amount=12000.0,
                channel="NEFT", narration="Unknown", counterparty_hint="Cust", reference=f"REF{txn_id}"
            )
            session.add(bt)
            add_gt("bank_transaction", txn_id, "UNMATCHED_RECEIPT")
            txn_id += 1
            
        # Trade links (cycles)
        links = []
        for i in range(100):
            links.append(TradeLink(
                from_gstin=random.choice(suppliers).gstin, to_gstin=random.choice(suppliers).gstin,
                value=random.uniform(10000, 100000), invoice_count=random.randint(1, 10), period="2026-09"
            ))
            
        # Plant 2 cycles
        # Cycle 1: 3 nodes (>= 5L)
        links.append(TradeLink(from_gstin=suppliers[15].gstin, to_gstin=suppliers[16].gstin, value=600000, invoice_count=5, period="2026-09"))
        links.append(TradeLink(from_gstin=suppliers[16].gstin, to_gstin=suppliers[17].gstin, value=600000, invoice_count=5, period="2026-09"))
        links.append(TradeLink(from_gstin=suppliers[17].gstin, to_gstin=suppliers[15].gstin, value=600000, invoice_count=5, period="2026-09"))
        
        # Cycle 2: 4 nodes
        links.append(TradeLink(from_gstin=suppliers[20].gstin, to_gstin=suppliers[21].gstin, value=550000, invoice_count=5, period="2026-09"))
        links.append(TradeLink(from_gstin=suppliers[21].gstin, to_gstin=suppliers[22].gstin, value=550000, invoice_count=5, period="2026-09"))
        links.append(TradeLink(from_gstin=suppliers[22].gstin, to_gstin=suppliers[23].gstin, value=550000, invoice_count=5, period="2026-09"))
        links.append(TradeLink(from_gstin=suppliers[23].gstin, to_gstin=suppliers[20].gstin, value=550000, invoice_count=5, period="2026-09"))
        
        for sup_idx in [15, 16, 17, 20, 21, 22, 23]:
            add_gt("supplier", sup_idx+1, "CIRCULAR_TRADING")

        for ln in links:
            session.add(ln)
            
        for g in gt:
            session.add(g)
            
        session.commit()
        
        # Export CSVs and JSON
        os.makedirs("data/exports", exist_ok=True)
        # We will write ground truth to json
        gt_export = []
        for g in gt:
            gt_export.append({"entity_type": g.entity_type, "entity_id": g.entity_id, "injected_issue_type": g.injected_issue_type, "note": g.note})
            
        with open("data/ground_truth.json", "w") as f:
            json.dump(gt_export, f, indent=2)

        def export_table(model, filename):
            rows = session.exec(select(model)).all()
            if not rows: return
            with open(f"data/exports/{filename}", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].model_dump().keys())
                writer.writeheader()
                for r in rows:
                    writer.writerow(r.model_dump())
        
        export_table(PurchaseBook, "purchase_books.csv")
        export_table(SupplierInvoice, "supplier_invoices.csv")
        export_table(GSTR2BEntry, "gstr2b_entries.csv")
        export_table(SalesInvoice, "sales_invoices.csv")
        export_table(BankTransaction, "bank_transactions.csv")
        export_table(TradeLink, "trade_links.csv")

if __name__ == "__main__":
    generate_data()
