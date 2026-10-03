# ITC Shield — Business Rules and Synthetic Data Spec

Source of truth for the rule engine and the data generator. If code and this file disagree, fix the code (or ask the human to change this file).

**Disclaimer:** simplified for a prototype. Rates in the rate table are illustrative and must be verified before any real use. UPI fee details were taken from public explainers of the NPCI notification and must be checked against the circular. Not tax or legal advice.

---

## 1. Glossary (use these words in UI text)

| Term | Plain meaning |
|---|---|
| ITC (input tax credit) | Tax we already paid to suppliers that we can deduct from our own GST payable |
| GSTR-2B | Government's auto-generated list of invoices our suppliers have filed about us |
| GSTR-3B | Our monthly summary return; due on the 20th of the next month |
| HSN / SAC | Product / service code that decides the GST rate |
| IGST | Tax on inter-state purchases. CGST + SGST apply to same-state purchases |
| MDR | Merchant Discount Rate: fee the merchant pays on certain UPI payments |
| At risk | ITC that depends on a supplier or the government and could be blocked or reversed |
| Needs a fix | Problem we or the supplier can correct (wrong rate, duplicate, typo) |
| Safe to claim | ITC with no open issue |

## 2. Constants (all in config, see ARCHITECTURE section 5)

AS_OF_DATE `2026-10-18` · open period `2026-09` · GSTR-3B due day 20 · GST rate cutover `2025-09-22` · payment window 180 days · warn at 30 days left · rounding tolerance ₹1 · approval threshold ₹50,000 · UPI MDR 0.4 percent above ₹2,000, capped at ₹300, effective `2026-10-15`, small-merchant exemption flag default false.

Return due date for a period `YYYY-MM` is the 20th of the following month. For `2026-09` that is `2026-10-20`.

## 3. Rate table (illustrative seed, `seed/rate_table.csv`)

Rate to apply = `rate_before` if invoice_date is before `2025-09-22`, else `rate_after`. Match by longest `hsn_prefix`.

| hsn_prefix | description | rate_before | rate_after |
|---|---|---|---|
| 4819 | Paper cartons and packaging | 12 | 5 |
| 6307 | Made-up textile articles | 12 | 5 |
| 8483 | Bearings and transmission parts | 28 | 18 |
| 8708 | Vehicle parts | 28 | 18 |
| 3923 | Plastic packaging | 18 | 18 |
| 3926 | Other plastic articles | 18 | 18 |
| 7318 | Fasteners | 18 | 18 |
| 7326 | Steel articles | 18 | 18 |
| 8536 | Electrical connectors | 18 | 18 |
| 9983 | Professional services (SAC) | 18 | 18 |
| 9965 | Goods transport (SAC) | 5 | 5 |

## 4. Rule catalog

Each finding stores `rule_id`, the inputs used and the numbers computed, so the UI evidence panel can show the working.

### R-MATCH-01 Missing in GSTR-2B
- Trigger: a purchase_books row has no match in GSTR-2B after all three passes.
- `amount_at_stake` = cgst + sgst + igst of the invoice. Issue type `MISSING_IN_GSTR2B`, bucket AT_RISK.
- Deadline = return due date of the invoice's `itc_period`. If already past, deadline = AS_OF_DATE.
- Action: `CHASE_SUPPLIER`; if supplier score is 70 or more, `HOLD_PAYMENT`.
- Confidence 1.0.

### R-MATCH-02 Missing in books
- Trigger: GSTR-2B row with no match in purchase_books.
- `amount_at_stake` = its tax. Type `MISSING_IN_BOOKS`, bucket NEEDS_FIX. Action `RECORD_INVOICE`. Confidence 0.9.

### R-MATCH-03 Low-confidence match
- Trigger: only an Amount-pass match (confidence 0.55). Type `AMOUNT_MISMATCH` with reason "matched on amount only, invoice numbers differ", bucket REVIEW, `amount_at_stake` 0.

### R-ITC-01 Cancelled or suspended supplier
- Trigger: supplier `gstin_status` is CANCELLED or SUSPENDED and invoice_date is on or after `status_changed_on` (invoices dated after the cancellation or suspension date; earlier invoices are not flagged).
- `amount_at_stake` = invoice tax. Type `SUPPLIER_GSTIN_CANCELLED`, bucket AT_RISK, severity CRITICAL, action `HOLD_PAYMENT`, deadline AS_OF_DATE. Confidence 1.0.
- If an invoice from this supplier also triggers R-MATCH-01, keep both findings but count the amount once in KPIs (max rule in ARCHITECTURE 9.1).

### R-TAX-01 Tax amount mismatch (books vs GSTR-2B)
- Trigger: matched pair where |books_tax − gstr2b_tax| > tolerance.
- `amount_at_stake` = max(0, books_tax − gstr2b_tax) (credit we booked but supplier did not report). If books tax is lower, stake is 0 and the reason says "supplier reported more than we booked".
- Type `AMOUNT_MISMATCH`, bucket NEEDS_FIX, action `ASK_CREDIT_NOTE` if books higher, else `CORRECT_BOOKS`. Confidence = match confidence.

### R-TAX-02 Wrong tax rate (date-aware)
- Expected rate = rate table lookup by HSN prefix and invoice_date (uses the 22 Sep 2025 cutover).
- Trigger: |charged_rate − expected_rate| > 0.01. Charged rate = `supplier_invoices.rate_pct` if available, else books `rate_pct`.
- `expected_tax = taxable_value × expected_rate / 100`; `charged_tax = taxable_value × charged_rate / 100`.
- `amount_at_stake` = max(0, charged_tax − expected_tax) for overcharge. For undercharge, stake 0 and bucket REVIEW with reason "charged less than expected; supplier may owe the difference".
- Type `WRONG_TAX_RATE`, bucket NEEDS_FIX (overcharge). Action `ASK_CREDIT_NOTE`. Confidence 0.95.
- Reason text must say whether the cause looks like the 22 Sep 2025 change: `charged_rate == rate_before and invoice_date >= cutover` means "old rate used after the 22 Sep 2025 change".
- Decoy: an invoice dated before the cutover at the old rate is correct and must not be flagged.

### R-TAX-03 Wrong tax type (IGST vs CGST+SGST)
- Place of supply = our state for purchases (goods delivered to us), so supplier state equal to ours means CGST+SGST; different means IGST.
- Trigger: books or invoice shows the wrong head.
- Type `WRONG_TAX_TYPE`, bucket NEEDS_FIX, `amount_at_stake` = invoice tax, action `ASK_CREDIT_NOTE`, confidence 0.95. (Document the simplification in the UI.)

### R-DUP-01 Duplicates
- Exact: same supplier gstin and same `invoice_no_norm` appear 2 or more times in books. Confidence 1.0.
- Fuzzy: same supplier, `token_sort_ratio` at least 90 on raw numbers, same taxable value, dates within 3 days. Confidence 0.85.
- Keep the earliest as the original; flag the rest. Type `DUPLICATE_INVOICE`, bucket NEEDS_FIX, `amount_at_stake` = tax of each duplicate, action `REMOVE_DUPLICATE`. Record status `DUPLICATE` on the extras.

### R-CUT-01 Period cutoff
- Trigger: invoice_date in the last 3 days of a month and either the books `itc_period` or the payment date falls in the next month, or the invoice appears in a different GSTR-2B period than its invoice month.
- Type `PERIOD_CUTOFF`, bucket REVIEW, stake 0, action `INVESTIGATE`. Reason: "timing difference between periods; confirm which period the credit belongs to". Confidence 0.8.

### R-CLK-01 180-day payment clock
- For each purchase invoice, paid amount = sum of matched payments. `unpaid_share = 1 − paid/total` (min 0).
- `days_elapsed = AS_OF_DATE − invoice_date`; `deadline = invoice_date + 180 days`; `days_left = 180 − days_elapsed`.
- Trigger when `unpaid_share > 0.01` and `days_left <= 30`.
- `amount_at_stake` = invoice tax × unpaid_share. Type `PAYMENT_180_DAY_RISK`, bucket AT_RISK.
- If `days_left >= 0`: action `PAY_NOW`, title "Pay supplier before the 180-day limit". If `days_left < 0`: action `REVERSE_ITC`, title "180-day limit passed; credit must be reversed". Confidence 1.0.

### R-UPI-01 UPI merchant fee
- Applies to sales receipts with channel `UPI` and txn_kind `P2M`, received on or after `UPI_MDR_EFFECTIVE`, amount strictly above ₹2,000, when the merchant is not exempt.
- `mdr(amount) = min(round(amount × 0.004, 2), 300)`.
- Expected settlement = invoice total − mdr. If received amount equals expected within tolerance: match type `MDR_ADJUSTED`, issue type `UPI_MDR_ADJUSTED`, bucket AUTO_RESOLVED. Evidence shows "₹3,000 invoice, 0.4% fee ₹12, deposit ₹2,988".
- If received is short and not explained by this rule (or the receipt predates the effective date): `UPI_SHORT_SETTLEMENT_UNEXPLAINED`, bucket REVIEW, stake = shortfall, action `INVESTIGATE`.
- Whether GST applies on the fee itself is not modelled; keep as config `UPI_MDR_GST_RATE` default 0 and a TODO note in the code.

### R-RND-01 Rounding
- Trigger: matched pair where 0 < |difference| ≤ ₹1. Type `ROUNDING_DIFF`, bucket AUTO_RESOLVED, status `MATCHED_ADJUSTED`.

### R-PAY-01 Unmatched payment and receipt
- Bank debit to a known supplier with no invoice match: `UNMATCHED_PAYMENT`, REVIEW, stake = amount, action `INVESTIGATE`.
- Bank credit with no sales match and no MDR explanation: `UNMATCHED_RECEIPT`, REVIEW.

### R-ANO-01 Split invoices
- Trigger: same supplier, invoice dates within a 2-day window, 2 or more invoices, each below `APPROVAL_THRESHOLD`, sum at or above it, and each at least 70 percent of the threshold.
- Type `SPLIT_INVOICE`, bucket REVIEW, stake 0, action `INVESTIGATE`, confidence 0.8. One finding per group; evidence lists all invoices.

### R-ANO-02 Statistical anomaly
- IsolationForest (`contamination=0.03`, `random_state=42`) on features: log(taxable_value), z-score of taxable value within supplier, round-amount flag (multiple of 1,000), days since the supplier's previous invoice, day of month.
- Only for invoices with no other finding. Type `STATISTICAL_ANOMALY`, REVIEW, stake 0, confidence = min(0.7, normalised anomaly score). Reason names the top feature that made it unusual.

### R-GRF-01 Circular trading
- Directed graph from `trade_links`. Cycles of length 3 to 5 with total value at or above ₹5,00,000 and every node in the cycle having at least one link inside the cycle.
- If any node in a cycle is one of our suppliers: finding per affected supplier, type `CIRCULAR_TRADING`, bucket REVIEW, stake 0, action `INVESTIGATE`, confidence 0.6. Wording: "part of a loop of invoices between the same firms; needs review". Never say fraud.

## 5. Supplier risk score (0 to 100, explainable)

| Factor | Weight | Normalisation |
|---|---|---|
| Missed or late filings in last 6 months | 30 | (6 − filings_on_time) / 6 |
| Share of our invoices missing in GSTR-2B | 25 | missing / total (cap 1) |
| Average filing delay | 15 | min(avg_delay_days / 30, 1) |
| Mismatch rate with us (amount, rate, duplicates) | 15 | issues / invoices (cap 1) |
| In a flagged circular-trading loop | 15 | 1 or 0 |

`score = sum(weight × normalised)`. If GSTIN is CANCELLED, score is 100 and the top factor reads "GSTIN cancelled". Store the contribution of each factor for the UI.

## 6. Synthetic dataset spec (generator, seed 42)

Business: "Meridian Components Pvt Ltd", Delhi (state code 07), fictional GSTIN with a fake PAN block.

| Table | Rows (approx) | Notes |
|---|---|---|
| suppliers | 40 | states: ~40% Delhi, rest Haryana, Maharashtra, Karnataka, Tamil Nadu, Uttar Pradesh |
| customers | 25 | |
| purchase_books | 520 | invoice dates 2025-07-01 to 2026-10-15; densest in last 3 months |
| supplier_invoices | ~520 | document view of the same invoices, with injected differences |
| gstr2b_entries | ~470 | what suppliers filed |
| sales_invoices | 420 | includes 40 UPI-paid invoices above ₹2,000 |
| bank_transactions | ~900 | debits to suppliers (some batch payments), credits from customers |
| trade_links | ~150 | includes 2 planted cycles |

Invoice numbers: write the same invoice 3 ways across sources for about 20 percent of rows (`INV/25-26/0045`, `45`, `INV-0045`).

### Planted issues (targets for the evaluation harness)

| Injection | Count | How |
|---|---|---|
| Clean records | ~80 percent | all sources agree |
| Missing in GSTR-2B | 14 | concentrated in 4 chronic late-filing suppliers |
| Ghost suppliers | 2 suppliers, ~6 invoices | GSTIN cancelled before invoice dates; never in GSTR-2B |
| Amount mismatch | 10 | books tax differs from GSTR-2B by 5 to 15 percent |
| Duplicates | 8 | 5 exact, 3 with fuzzy invoice-number variants |
| Wrong rate | 10 | 6 stale old rates after 22 Sep 2025 (HSN 4819, 6307, 8483, 8708), 4 other wrong rates |
| Decoys (must NOT be flagged) | 8 | invoices dated 15 to 21 Sep 2025 at the old rate; correct |
| Wrong tax type | 4 | IGST charged on same-state purchase or the reverse |
| Rounding | 15 | differences of ₹0.01 to ₹1.00 |
| Period cutoff | 6 | invoice 29 to 30 of a month, payment or booking next month |
| 180-day risk | 8 | unpaid invoices dated 150 to 200 days before AS_OF_DATE |
| Split invoices | 3 groups × 3 invoices | ₹38,000 to ₹49,500 each, same day, same supplier |
| Circular trading | 2 cycles (3 nodes and 4 nodes) | each includes 1 to 2 of our suppliers |
| Missing in books | 6 | in GSTR-2B, never booked |
| Unmatched payment | 5 | debits with no invoice |
| UPI MDR receipts | 20 | UPI above ₹2,000 on or after 2026-10-15 settled net of MDR (including one at the ₹300 cap on ₹75,000+) |
| UPI decoys | 8 | UPI above ₹2,000 before 2026-10-15 settled in full, plus UPI of ₹2,000 or less settled in full |
| UPI unexplained short | 3 | short by amounts that are not the MDR |
| Unmatched receipts | 4 | |
| Statistical anomalies | 6 | extreme amounts for that supplier |

`ground_truth.json` lists `{entity_type, entity_id, injected_issue_type}` for every planted item and decoys with `injected_issue_type = null`. Rules must never read it.

## 7. Plain-language reason templates (fallback text)

Keep sentences short, avoid jargon, always include the rupee figure and the next step. Examples:

- MISSING_IN_GSTR2B: "{supplier} has not reported invoice {no} yet, so ₹{amt} of tax credit cannot be claimed. Chase them before the {due} filing."
- WRONG_TAX_RATE (stale): "This invoice is dated {date}, after the 22 Sep 2025 rate change, but charges {charged}% instead of {expected}%. Ask for a credit note for ₹{amt}."
- PAYMENT_180_DAY_RISK: "Invoice {no} is unpaid and {days} days remain of the 180-day limit. Pay by {deadline} to keep ₹{amt} of credit."
- UPI_MDR_ADJUSTED: "Deposit is ₹{fee} short of the invoice because of the 0.4% UPI merchant fee. This is expected, not an error."
- CIRCULAR_TRADING: "{supplier} is part of a loop of invoices between the same firms. This needs a human review, it is not proof of wrongdoing."