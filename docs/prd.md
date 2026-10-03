# ITC Shield — Product Requirements Document

Team Fintastic · Fintechstico prototype round · PS2: Intelligent Tax Reconciliation
Version 1.0 · Prototype window about 10 to 12 hours · Status: design template pending

---

## 1. Summary

ITC Shield is a pre-filing GST reconciliation tool. Existing tools list mismatches. ITC Shield tells a finance team **what each mismatch costs in rupees, why it happened, and what to do before the return is filed**, ranked in one action list called the ITC Recovery Queue.

One-line pitch: *"Other tools show what is wrong. We show what it costs and what to do about it, before you file."*

## 2. Problem

A business keeps three sets of records that rarely agree: its own books, supplier invoices and GSTR-2B (what suppliers filed), and the bank. When they differ, the company overpays tax, loses input tax credit (ITC), or gets a notice. Three live causes:

1. A supplier does not file, so ITC is blocked.
2. GST rates changed on 22 Sep 2025, so invoices at old rates are wrong.
3. A UPI merchant fee (0.4 percent above ₹2,000) starts 15 Oct 2026, so bank deposits arrive short and look like errors.

Reconciliation tools stop at "these 40 rows do not match". Finance teams need a ranked to-do list with money attached.

## 3. Goals and non-goals

### Goals
- G1. Cover every PS2 requirement: reconciliation, mismatch and duplicate detection, tax verification, missing and unmatched detection, anomaly detection, liability analysis, dashboard.
- G2. Make rupees-at-stake the organising idea of the product.
- G3. Be explainable: every finding shows the rule, the numbers and the records behind it.
- G4. Be demo-reliable: deterministic, offline-capable, fast.
- G5. Prove accuracy honestly using planted errors with ground truth.

### Non-goals
- Real GSTN or e-invoice integration, filing returns, or real tax advice.
- Multi-tenant auth, user accounts, roles.
- RCM, ITC reversals other than the 180-day rule, TDS/TCS, composition scheme, multiple registrations.
- Training ML on real data. No claims of real-world accuracy.

## 4. Users and scenarios

**Primary user: finance manager at a mid-size manufacturer** (Meridian Components Pvt Ltd in the demo). Files GSTR-3B monthly, handles 500+ purchase invoices a month, hates surprise notices.

Scenarios:
- S1. Two days before the due date, she opens the queue and sees ₹6.8 L at risk. The top item is a supplier who has not filed. She sends the drafted follow-up.
- S2. She sees invoices from late September charged at the old 12 percent rate on an item now at 5 percent, and asks the supplier for credit notes.
- S3. An invoice is 11 days from the 180-day payment limit. She pays it and the item resolves.
- S4. UPI deposits are a few rupees short on big sales. The tool explains the fee instead of flagging errors.
- S5. An auditor asks when a mismatch was caught. She shows the audit trail.

## 5. Functional requirements

Priority: **M** must-have, **S** should-have, **C** could-have (stretch).

### 5.1 Data and ingestion
- FR-1 (M). Generate a synthetic dataset (spec in BUSINESS_RULES section 6) deterministically from a seed, with planted errors and a ground-truth file.
- FR-2 (M). Load data into SQLite and expose the four record sets plus sales and trade links.
- FR-3 (S). CSV upload for each record set with schema validation and clear error messages.
- FR-4 (C). Invoice image or PDF reader using a vision model that writes into `supplier_invoices` and flags ambiguous fields. Demo with 3 to 5 sample invoices.

### 5.2 Reconciliation
- FR-5 (M). Match books to GSTR-2B and to invoice documents using exact, fuzzy and amount passes, with a confidence score per match.
- FR-6 (M). Match bank debits to supplier invoices (one-to-one and batch payments) and bank credits to sales invoices.
- FR-7 (M). Assign every source record one status: matched, matched with adjustment, discrepant, unmatched, duplicate.

### 5.3 Checks
- FR-8 (M). Detect mismatches in amount, date, invoice ID and tax values; auto-resolve rounding up to ₹1.
- FR-9 (M). Detect exact and near-duplicate invoices.
- FR-10 (M). Verify tax: rate by HSN and invoice date (including the 22 Sep 2025 cutover) and tax type by state.
- FR-11 (M). Detect missing and unmatched transactions: missing in GSTR-2B, missing in books, unmatched payments and receipts.
- FR-12 (M). 180-day payment clock with days left and deadline.
- FR-13 (M). UPI merchant fee awareness: explain short settlements, respecting the effective date, threshold and cap.
- FR-14 (M). Anomaly detection: split invoices (rule) and statistical outliers (IsolationForest).
- FR-15 (S). Circular-trading detection on the simulated trade-links feed, with supplier exposure.
- FR-16 (M). Explainable supplier risk score with per-factor contributions.

### 5.4 Decisions
- FR-17 (M). Produce the ITC Recovery Queue: one row per issue with type, rupees at stake, priority, deadline, days left, plain-language reason, recommended action, evidence.
- FR-18 (M). KPI buckets for a period: Safe to claim, At risk, Needs a fix; integrity equation holds.
- FR-19 (M). Tax liability analysis: output tax, ITC claimable now, net payable now, net payable if all issues are recovered, cash impact.
- FR-20 (M). Status workflow per issue: Open, Actioned, Resolved, Dismissed.

### 5.5 Assistance
- FR-21 (S). Plain-language explanation of any issue, and a vendor follow-up draft, via LLM with deterministic template fallback.
- FR-22 (M). Tamper-evident audit trail with hash chaining and a verify endpoint.
- FR-23 (S). Evaluation page showing precision and recall per issue type against planted errors.

### 5.6 Dashboard and screens
- FR-24 (M). Dashboard: KPI cards, reconciliation status chart (matched, unmatched, duplicate, discrepant), liability panel, top 5 queue items, auto-matched strip (rounding and UPI fee).
- FR-25 (M). Recovery Queue page: filter by bucket, type, severity, status, period; sort by priority; detail drawer with evidence, explanation, draft and status buttons.
- FR-26 (M). Reconciliation Explorer: per-source status counts and a paged record table with the matched counterpart.
- FR-27 (S). Suppliers page: score, factors, issues; network graph with cycles highlighted and labelled "simulated".
- FR-28 (M). Audit page.
- FR-29 (S). Rules and data page: rate table, active config, seed and run buttons.

## 6. Differentiators (what we tell judges)

1. **Rupee-ranked action queue** (the main one). Every problem has a cost, a cause and a next step.
2. **Date-aware tax checks.** Knows the 22 Sep 2025 GST rate change and the 15 Oct 2026 UPI fee, so decoys are not flagged.
3. **180-day payment clock** that warns before a credit reversal.
4. **Supplier risk and loop spotter**, explainable, labelled for review.
5. **Measured accuracy** on planted errors, honestly scoped.
Supporting: tamper-evident audit trail, plain-language explanations.

## 7. UX requirements

- Plain language; avoid jargon, or explain it inline (glossary in BUSINESS_RULES).
- Every money figure in Indian format (₹1,80,000) and lakh shorthand on cards (₹6.8 L).
- Every number on a card must be traceable by click to the rows behind it.
- Status colours: green safe, maroon at risk, orange needs fix, neutral review.
- Loading, empty and error states for every view.
- Responsive down to a 1280 px laptop; mobile is not required.
- Visual design: **pending a design template from the team**. Build with design tokens so the template can be applied by changing tokens and layout components. Until then use a clean neutral light theme with warm accents (cream, orange, deep brown, maroon) to match the submission deck.

## 8. Data requirements

See BUSINESS_RULES section 6 and ARCHITECTURE section 6. All data synthetic, fictional names and GSTINs with obviously fake PAN blocks. No real personal or company data anywhere.

## 9. Success criteria (demo-day checklist)

| ID | Criterion | Target |
|---|---|---|
| SC-1 | One command seeds data and runs the pipeline | under 15 s end to end |
| SC-2 | Planted-error recall (rule-based types) | at least 90 percent |
| SC-3 | Planted-error precision, decoys not flagged | at least 85 percent |
| SC-4 | KPI integrity equation holds | exact within ₹1 |
| SC-5 | Queue top item is the largest urgent AT_RISK item | yes |
| SC-6 | Works with no internet and `LLM_PROVIDER=none` | yes |
| SC-7 | 3-minute demo script runs without touching code | yes |
| SC-8 | Audit verify returns valid, and detects a manually tampered row | yes |

## 10. Scope tiers and cut list

Build order follows PROMPTS.md. If time runs short, cut from the bottom:

1. FR-4 invoice reader (stretch, already optional)
2. FR-27 network graph UI (keep the supplier table)
3. FR-21 LLM drafts (templates are enough)
4. FR-14 statistical anomaly ML (keep split-invoice rule)
5. FR-3 CSV upload

Never cut: FR-5 to FR-13, FR-17 to FR-20, FR-22, FR-24, FR-25.

## 11. Assumptions

- A1. Single business registration; monthly filer.
- A2. Rate table is illustrative; real use needs verified rates by HSN.
- A3. UPI fee parameters come from public explainers of the NPCI notification effective 15 Oct 2026; verify against the circular. GST on the fee is not modelled.
- A4. Trade links between suppliers are simulated; in reality this data would come from government analytics, not from one business.
- A5. 180-day rule simplified: payment to supplier within 180 days of invoice date, proportional ITC at stake for the unpaid part.
- A6. Place of supply for purchases is our state.

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Over-scoping in 10 to 12 hours | stage gating, cut list, run frontend work in parallel with backend |
| Judges doubt synthetic accuracy numbers | label as planted-error accuracy; show decoys; show the rule and evidence behind each finding |
| Tax details wrong | illustrative labels, config-driven rates, disclaimer |
| LLM or network failure in demo | template fallback, offline mode |
| Design template arrives late | token-based styling, design stage is separate and last before polish |

## 13. Timeline (about 11 hours, with parallel work)

| Stage | Work | Hours |
|---|---|---|
| 0 | Repo, docs, rules, scaffolds, API contract and fixtures | 0.5 |
| 1 | Data models and synthetic generator with ground truth | 1.25 |
| 2 | Matching engine | 1.75 |
| 3 | Rule engine | 1.5 |
| 4 | Risk layer | 1.25 |
| 5 | Decision engine, liability, audit, evaluation | 1.25 |
| 6 | LLM layer and API completion | 0.75 |
| 7 | Frontend build (parallel from Stage 1) | 2.5 |
| 8 | Apply design template | 1.0 |
| 9 | Integration, demo script, README | 0.75 |
| S | Stretch: invoice reader | 1.0 |

Critical path with one agent working backend and a second on frontend: about 10 to 11 hours of wall time.

## 14. Open items

- Design template and DESIGN.md from the team (pending).
- Confirm demo machine and whether internet and an LLM key will be available.
- Confirm UPI fee details against the NPCI circular before final demo.