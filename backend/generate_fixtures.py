import json
import os

os.makedirs("backend/app/api/fixtures", exist_ok=True)

queue_items = [
    {
        "id": 1,
        "rule_id": "R-MATCH-01",
        "issue_type": "MISSING_IN_GSTR2B",
        "bucket": "AT_RISK",
        "severity": "HIGH",
        "title": "Invoice not in GSTR-2B",
        "plain_reason": "Zenith Traders has not reported this invoice, so the tax credit cannot be claimed yet.",
        "amount_at_stake": 180000.0,
        "priority_score": 270000.0,
        "confidence": 1.0,
        "deadline": "2026-10-20",
        "days_left": 2,
        "recommended_action": "CHASE_SUPPLIER",
        "entity": {
            "type": "purchase_invoice",
            "id": 412,
            "invoice_no": "INV/25-26/0045",
            "invoice_date": "2026-09-12",
            "supplier_id": 9,
            "supplier_name": "Zenith Traders"
        },
        "evidence": [
            {"label": "Books tax", "value": "180000.00", "source": "purchase_books#412"}
        ],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 2,
        "rule_id": "R-CLK-01",
        "issue_type": "PAYMENT_180_DAY_RISK",
        "bucket": "AT_RISK",
        "severity": "HIGH",
        "title": "Pay supplier before the 180-day limit",
        "plain_reason": "Invoice INV-01 is unpaid and 10 days remain of the 180-day limit. Pay by 2026-10-28 to keep ₹50000.0 of credit.",
        "amount_at_stake": 50000.0,
        "priority_score": 75000.0,
        "confidence": 1.0,
        "deadline": "2026-10-28",
        "days_left": 10,
        "recommended_action": "PAY_NOW",
        "entity": {
            "type": "purchase_invoice",
            "id": 413,
            "invoice_no": "INV-01",
            "invoice_date": "2026-05-01",
            "supplier_id": 10,
            "supplier_name": "Acme Corp"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 3,
        "rule_id": "R-TAX-02",
        "issue_type": "WRONG_TAX_RATE",
        "bucket": "NEEDS_FIX",
        "severity": "MEDIUM",
        "title": "Wrong tax rate charged",
        "plain_reason": "This invoice is dated 2026-09-10, after the 22 Sep 2025 rate change, but charges 18% instead of 5%. Ask for a credit note for ₹13000.0.",
        "amount_at_stake": 13000.0,
        "priority_score": 13000.0,
        "confidence": 0.95,
        "deadline": None,
        "days_left": None,
        "recommended_action": "ASK_CREDIT_NOTE",
        "entity": {
            "type": "purchase_invoice",
            "id": 414,
            "invoice_no": "INV-02",
            "invoice_date": "2026-09-10",
            "supplier_id": 11,
            "supplier_name": "Paper Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 4,
        "rule_id": "R-DUP-01",
        "issue_type": "DUPLICATE_INVOICE",
        "bucket": "NEEDS_FIX",
        "severity": "MEDIUM",
        "title": "Duplicate invoice found",
        "plain_reason": "This invoice appears to be a duplicate.",
        "amount_at_stake": 25000.0,
        "priority_score": 25000.0,
        "confidence": 1.0,
        "deadline": None,
        "days_left": None,
        "recommended_action": "REMOVE_DUPLICATE",
        "entity": {
            "type": "purchase_invoice",
            "id": 415,
            "invoice_no": "INV-03",
            "invoice_date": "2026-09-11",
            "supplier_id": 12,
            "supplier_name": "Steel Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 5,
        "rule_id": "R-ANO-01",
        "issue_type": "SPLIT_INVOICE",
        "bucket": "REVIEW",
        "severity": "LOW",
        "title": "Possible split invoices",
        "plain_reason": "Multiple invoices just under the approval threshold on the same day.",
        "amount_at_stake": 0.0,
        "priority_score": 800.0,
        "confidence": 0.8,
        "deadline": None,
        "days_left": None,
        "recommended_action": "INVESTIGATE",
        "entity": {
            "type": "purchase_invoice",
            "id": 416,
            "invoice_no": "INV-04",
            "invoice_date": "2026-09-12",
            "supplier_id": 13,
            "supplier_name": "Parts Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 6,
        "rule_id": "R-GRF-01",
        "issue_type": "CIRCULAR_TRADING",
        "bucket": "REVIEW",
        "severity": "LOW",
        "title": "Circular trading loop detected",
        "plain_reason": "Parts Co is part of a loop of invoices between the same firms. This needs a human review, it is not proof of wrongdoing.",
        "amount_at_stake": 0.0,
        "priority_score": 600.0,
        "confidence": 0.6,
        "deadline": None,
        "days_left": None,
        "recommended_action": "INVESTIGATE",
        "entity": {
            "type": "supplier",
            "id": 13,
            "invoice_no": None,
            "invoice_date": None,
            "supplier_id": 13,
            "supplier_name": "Parts Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    },
    {
        "id": 7,
        "rule_id": "R-ITC-01",
        "issue_type": "SUPPLIER_GSTIN_CANCELLED",
        "bucket": "AT_RISK",
        "severity": "CRITICAL",
        "title": "Supplier GSTIN Cancelled",
        "plain_reason": "Supplier GSTIN cancelled before invoice date.",
        "amount_at_stake": 450000.0,
        "priority_score": 450000.0,
        "confidence": 1.0,
        "deadline": "2026-10-18",
        "days_left": 0,
        "recommended_action": "HOLD_PAYMENT",
        "entity": {
            "type": "purchase_invoice",
            "id": 417,
            "invoice_no": "INV-05",
            "invoice_date": "2026-09-13",
            "supplier_id": 14,
            "supplier_name": "Ghost Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    }
]

for i in range(8, 13):
    queue_items.append({
        "id": i,
        "rule_id": "R-MATCH-02",
        "issue_type": "MISSING_IN_BOOKS",
        "bucket": "NEEDS_FIX",
        "severity": "LOW",
        "title": "Missing in books",
        "plain_reason": "Supplier reported an invoice we haven't booked.",
        "amount_at_stake": 1000.0 * i,
        "priority_score": 1000.0 * i,
        "confidence": 0.9,
        "deadline": None,
        "days_left": None,
        "recommended_action": "RECORD_INVOICE",
        "entity": {
            "type": "gstr2b_entry",
            "id": 500 + i,
            "invoice_no": f"INV-{i}",
            "invoice_date": "2026-09-15",
            "supplier_id": 15,
            "supplier_name": "General Co"
        },
        "evidence": [],
        "status": "OPEN",
        "explanation": None,
        "draft": None
    })

with open("backend/app/api/fixtures/queue.json", "w") as f:
    json.dump(queue_items, f, indent=2)

status_breakdown = {
    "matched": 350,
    "matched_adjusted": 20,
    "discrepant": 30,
    "unmatched": 15,
    "duplicate": 5
}

liability = {
    "output_tax": 5000000.0,
    "itc_claim_now": 4260000.0,
    "itc_if_all_recovered": 5060000.0,
    "net_payable_now": 740000.0,
    "net_payable_if_recovered": 0.0,
    "cash_impact_of_issues": 740000.0
}

summary = {
    "safe_to_claim": 4260000.0,
    "at_risk": 680000.0,
    "needs_fix": 120000.0,
    "status_breakdown": status_breakdown,
    "liability": liability,
    "top5_queue": queue_items[:5]
}

with open("backend/app/api/fixtures/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

status_response = {
    "purchase_books": status_breakdown,
    "supplier_invoices": status_breakdown,
    "gstr2b_entries": status_breakdown,
    "sales_invoices": status_breakdown,
    "bank_transactions": status_breakdown
}

with open("backend/app/api/fixtures/status.json", "w") as f:
    json.dump(status_response, f, indent=2)

records = {
    "items": [{"id": 1, "source": "purchase_books", "status": "MATCHED", "data": {"invoice_no": "123"}}],
    "total": 1,
    "page": 1,
    "page_size": 50
}
with open("backend/app/api/fixtures/records.json", "w") as f:
    json.dump(records, f, indent=2)

suppliers = [
    {"id": 9, "name": "Zenith Traders", "gstin": "07ZZZZZ9999Z1Z1", "score": 85.5}
]
with open("backend/app/api/fixtures/suppliers.json", "w") as f:
    json.dump(suppliers, f, indent=2)

supplier_detail = {
    "id": 9, "name": "Zenith Traders", "gstin": "07ZZZZZ9999Z1Z1", "score": 85.5,
    "factors": {"missed_filings": 0.5},
    "issues": [queue_items[0]]
}
with open("backend/app/api/fixtures/supplier_detail.json", "w") as f:
    json.dump(supplier_detail, f, indent=2)

graph = {
    "nodes": [
        {"id": "13", "name": "Parts Co", "is_supplier": True, "val": 100},
        {"id": "S1", "name": "Shell 1", "is_supplier": False, "val": 50},
        {"id": "S2", "name": "Shell 2", "is_supplier": False, "val": 50}
    ],
    "edges": [
        {"source": "13", "target": "S1", "val": 10},
        {"source": "S1", "target": "S2", "val": 10},
        {"source": "S2", "target": "13", "val": 10}
    ],
    "cycles": [
        {"nodes": ["13", "S1", "S2"], "value": 500000.0}
    ]
}
with open("backend/app/api/fixtures/graph.json", "w") as f:
    json.dump(graph, f, indent=2)

with open("backend/app/api/fixtures/liability.json", "w") as f:
    json.dump(liability, f, indent=2)
    
audit = [
    {"id": 1, "ts": "2026-10-18T10:00:00Z", "actor": "system", "action": "RUN_STARTED", "entity_type": "run", "entity_id": 1, "payload_json": "{}", "hash": "abc"}
]
with open("backend/app/api/fixtures/audit.json", "w") as f:
    json.dump(audit, f, indent=2)
    
eval_res = {
    "metrics": {
        "MISSING_IN_GSTR2B": {"precision": 0.95, "recall": 0.9}
    }
}
with open("backend/app/api/fixtures/eval.json", "w") as f:
    json.dump(eval_res, f, indent=2)
    
rules = {
    "active_config": {"AS_OF_DATE": "2026-10-18"},
    "rate_table": [{"hsn_prefix": "4819", "rate_before": 12, "rate_after": 5}]
}
with open("backend/app/api/fixtures/rules.json", "w") as f:
    json.dump(rules, f, indent=2)

run_summary = {
    "run_id": 1,
    "started_at": "2026-10-18T10:00:00Z",
    "duration_ms": 1500,
    "period": "2026-09",
    "counts": {"issues": 12}
}
with open("backend/app/api/fixtures/run_summary.json", "w") as f:
    json.dump(run_summary, f, indent=2)

audit_verify = {"valid": True, "broken_at_id": None}
with open("backend/app/api/fixtures/audit_verify.json", "w") as f:
    json.dump(audit_verify, f, indent=2)
