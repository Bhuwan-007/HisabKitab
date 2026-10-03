# ITC Shield — Staged Prompts for Antigravity

Team Fintastic · about 10 to 12 hours · copy each prompt block into a **new** agent conversation, in order.

---

## 0. Before you start (5 minutes)

1. Create the repo folder `itc-shield/` and put the docs in `itc-shield/docs/`: `PRD.md`, `ARCHITECTURE.md`, `BUSINESS_RULES.md`, `RULES.md`, `PROMPTS.md`.
2. Copy **Part 1** of `docs/RULES.md` into `itc-shield/AGENTS.md`.
3. `git init`, first commit "docs".
4. Open the `itc-shield/` folder as the workspace in Antigravity.
5. Create a free Gemini API key only if you want live LLM text (optional; the app works without it).
6. Mode tip: if your build offers Planning and Fast modes, use Planning for stages 1 to 5 and 7, Fast for small fixes.

### Standard context line (start every prompt with it)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.
```

(Each prompt below already includes it. If your Antigravity build does not resolve `@` mentions, replace them with plain paths.)

### Stage map

| Stage | Name | Folder owned | Est. | Depends on |
|---|---|---|---|---|
| 0 | Skeleton and API contract with stub data | `backend/` | 0.5 h | docs |
| 1 | Data models and synthetic generator | `backend/` | 1.25 h | 0 |
| 2 | Matching engine | `backend/` | 1.75 h | 1 |
| 3a | Rules: tax, duplicates, missing, cutoff | `backend/` | 0.9 h | 2 |
| 3b | Rules: 180-day clock, UPI fee, payments | `backend/` | 0.6 h | 2 |
| 4 | Risk layer: supplier score, anomalies, graph | `backend/` | 1.25 h | 3 |
| 5 | Decision engine, pipeline, audit, evaluation | `backend/` | 1.25 h | 4 |
| 6 | LLM layer and API completion | `backend/` | 0.75 h | 5 |
| 7a | Frontend scaffold and Dashboard | `frontend/` | 1 h | 0 (stub API) |
| 7b | Recovery Queue and issue drawer | `frontend/` | 1 h | 7a |
| 7c | Explorer, Suppliers, Audit, Rules pages | `frontend/` | 0.75 h | 7b |
| 8 | Apply design template | `frontend/` | 1 h | 7c and DESIGN.md |
| 9 | Integration, demo script, README | both | 0.75 h | 6, 8 |
| S | Stretch: invoice image reader | both | 1 h | 9 |

**Parallel plan:** after Stage 0 is committed, run Stage 7a to 7c in a second agent session on `frontend/` while backend stages 1 to 6 run in the first. Both use the stub API contract. Merge by committing to different folders. Do not run two agents on the same folder.

**Cut list if late** (cut from the bottom): Stage S, network graph UI in 7c, LLM drafts in 6, statistical anomaly ML in 4, CSV upload in 6.

---

## Stage 0 — Skeleton and API contract (0.5 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 0: Backend skeleton and a stub API contract. Folder you own: backend/ and scripts/.

Goal: a running FastAPI app where every endpoint in ARCHITECTURE section 12 exists, validates with real Pydantic schemas, and returns realistic stub data from fixture files. The frontend will be built against this before the real engine exists.

Tasks:
1. Create backend/ with requirements.txt (fastapi, uvicorn, sqlmodel, pandas, rapidfuzz, scikit-learn, networkx, pydantic, python-dotenv, pytest, httpx) and a Python 3.11 virtualenv instruction in README stub.
2. Create app/config.py with every config key from ARCHITECTURE section 5, loaded from environment with the listed defaults. Add .env.example.
3. Create app/schemas.py containing all enums from ARCHITECTURE 6.4 and Pydantic response models for: HealthResponse, QueueItem (exactly the shape in ARCHITECTURE section 12), QueueDetail, SummaryResponse (KPI cards, status breakdown, liability, top5), ReconStatusResponse, RecordsPage, SupplierSummary, SupplierDetail, GraphResponse (nodes, edges, cycles), LiabilityResponse, AuditRow, AuditVerify, EvaluationResponse, RulesResponse, RunSummary.
4. Create app/db.py (SQLite engine, session dependency) and an empty app/models.py placeholder (tables come in Stage 1).
5. Create fixtures in app/api/fixtures/*.json that are consistent with each other and with BUSINESS_RULES. Use the demo story: business Meridian Components, period 2026-09, as-of 2026-10-18. Include 12 queue items covering at least these types: MISSING_IN_GSTR2B (Zenith Traders, ₹1,80,000), PAYMENT_180_DAY_RISK, WRONG_TAX_RATE (18% charged, now 5%), DUPLICATE_INVOICE, SPLIT_INVOICE, CIRCULAR_TRADING, SUPPLIER_GSTIN_CANCELLED. KPI example: Safe to claim 42.6 L, At risk 6.8 L, Needs a fix 1.2 L. Include a status breakdown and a small graph with one cycle.
6. Create routers under app/api/ for every endpoint in ARCHITECTURE section 12. Each returns its fixture (PATCH /queue/{id} should update an in-memory copy). Mark each stub with a comment STUB: replace in stage N.
7. app/main.py: mount routers under /api, CORS for http://localhost:5173 only, JSON error format from AGENTS.md.
8. Write tests/test_stub_api.py that calls every endpoint with FastAPI TestClient and validates the response against its schema.
9. Add scripts/run_backend.sh (uvicorn with reload on port 8000).

Verify (run and paste output): cd backend && pytest -q ; start the server and curl http://localhost:8000/api/health and http://localhost:8000/api/queue ; open /docs and confirm all endpoints are listed.

Finish with the summary format from AGENTS.md.
```

Commit and tag `stage-0-done`. Start the frontend session now (Stage 7a) in parallel.

---

## Stage 1 — Data models and synthetic generator (1.25 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 1: Data models and the synthetic data generator. Folder you own: backend/app/models.py, backend/app/seed/, backend/app/ingest/, backend/tests/.

Goal: deterministic synthetic data for Meridian Components with planted, labelled errors, loaded into SQLite.

Tasks:
1. Implement every table in ARCHITECTURE section 6 as SQLModel classes in app/models.py (including audit_log, issues, matches, record_status, supplier_scores, llm_cache, ground_truth, recon_runs). Add create_all in db.py.
2. Create seed/rate_table.csv from BUSINESS_RULES section 3 and load it into rate_table.
3. Implement ingest/normalize.py: normalize_invoice_no exactly as ARCHITECTURE 7 describes, validate_gstin, and helpers for rounding and Indian number formatting (backend side, for text templates later). Test with the examples INV/25-26/0045, 45, INV-0045, 0045 all returning 45.
4. Implement seed/generator.py and seed/injections.py. Generate a clean world first (suppliers, customers, purchase books, matching supplier invoices, GSTR-2B, sales, bank transactions, trade links), then apply the planted issues and decoys listed in BUSINESS_RULES section 6 with the stated counts. Write every planted item and decoy to ground_truth (decoys have injected_issue_type null). Use RANDOM_SEED. Use clearly fake GSTINs (PAN block ZZZZZ9999Z pattern) and fictional supplier names.
5. For about 20 percent of rows, write the invoice number in different raw formats across sources (see BUSINESS_RULES 6).
6. Make sure dates respect AS_OF_DATE: data from 2025-07-01 to 2026-10-15, densest in the last 3 months; UPI MDR receipts on or after 2026-10-15; decoys per spec.
7. Export CSV copies to backend/data/exports/ and ground_truth.json to backend/data/.
8. Replace the STUB for POST /api/data/seed with a real implementation (reset DB, regenerate, return row counts per table) and write an audit-free simple version for now (audit comes in stage 5).
9. scripts/seed.sh that runs the generator from the command line.

Tests (tests/test_seed.py): row counts within 5 percent of the spec; determinism (two runs with the same seed give identical CSV hashes); every injection count in ground_truth equals the spec; decoys exist; no supplier GSTIN equals the business GSTIN; invoice-number variants exist for at least 15 percent of rows; at least one UPI receipt exactly at the ₹300 cap.

Verify (paste output): bash scripts/seed.sh ; pytest -q ; print a table of ground_truth counts by injected_issue_type.

Finish with the summary format from AGENTS.md.
```

---

## Stage 2 — Matching engine (1.75 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 2: The matching engine. Folder you own: backend/app/matching/ and backend/tests/.

Goal: link records across sources with a confidence score, using each record at most once per pass.

Tasks:
1. matching/invoice_match.py: implement match_invoices(dataset) with the three passes in ARCHITECTURE section 7 (exact, fuzzy, amount) for purchase_books vs gstr2b_entries, and again for purchase_books vs supplier_invoices. Return Match dataclasses with left_type, left_id, right_type, right_id, match_type, confidence, diffs (taxable_diff, tax_diff, date_diff_days, invoice_no_similarity).
2. matching/payment_match.py: implement match_payments(dataset): (a) bank debits to supplier invoices, one to one by reference or supplier name similarity plus amount; (b) one-to-many batch payments covering 2 to 3 open invoices of the same supplier within 60 days; (c) bank credits to sales invoices by amount. Do NOT implement the UPI fee logic yet; leave a clearly marked hook function apply_upi_adjustment(...) that returns None, to be filled in stage 3b.
3. Use a dataset loader (ingest/loaders.py: load_all) that returns typed pandas DataFrames from the DB.
4. Performance: use blocking by supplier_gstin so matching 500 rows runs in under 2 seconds. No nested full-table loops.
5. Persist matches to the matches table through a function save_matches(run_id, matches).
6. Add a small report function match_report(matches, dataset) that prints counts: matched by type, unmatched books, unmatched GSTR-2B, unmatched bank debits and credits.

Tests: normalization-driven exact matches (INV/25-26/0045 vs 45 for the same supplier); no cross-supplier matches; fuzzy match with a typo; amount-pass flagged confidence 0.55; one record is never matched twice; a batch payment matches 2 invoices; a duplicate invoice in books matches only one GSTR-2B row.

Verify (paste output): seed then run match_report on the seeded DB. Expected shape: books to GSTR-2B matched is roughly 88 to 93 percent of books; unmatched books roughly equals planted Missing-in-GSTR-2B plus ghost-supplier invoices plus duplicates; unmatched GSTR-2B roughly equals planted Missing-in-books. Explain any large gap.

Finish with the summary format from AGENTS.md.
```

---

## Stage 3a — Rules: tax, duplicates, missing, cutoff (0.9 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 3a: Rule modules for tax and records. Folder you own: backend/app/rules/ and backend/tests/.

Implement these rules exactly as BUSINESS_RULES section 4 specifies, each as a module exposing run(dataset, matches, cfg) -> list[Finding]. Finding fields: rule_id, issue_type, entity_type, entity_id, supplier_id, amount_at_stake, confidence, evidence (list of label, value, source), deadline, action. Put the Finding dataclass and Evidence in rules/base.py.

- missing.py: R-MATCH-01 (missing in GSTR-2B, incl. deadline from the period due date), R-MATCH-02 (missing in books), R-MATCH-03 (low confidence match), and R-ITC-01 (cancelled or suspended supplier).
- tax_rate.py: R-TAX-01 (tax amount mismatch) and R-TAX-02 (wrong rate, date-aware using the rate table and GST_RATE_CUTOVER; handle overcharge vs undercharge; reason text must say when the old rate was used after the cutover).
- tax_type.py: R-TAX-03 (IGST vs CGST+SGST by state).
- duplicates.py: R-DUP-01 (exact and fuzzy duplicates, keep earliest, flag the rest).
- cutoff.py: R-CUT-01 (period cutoff) and R-RND-01 (rounding auto-resolve).

Requirements:
- Read thresholds from config, rates from the rate_table, never hard-code.
- Evidence must include the numbers used (taxable value, charged rate, expected rate, charged tax, expected tax, etc.).
- Decoy safety is a hard requirement: an invoice dated before 2025-09-22 charged the old rate must produce no finding.
- Add rules/__init__.py with run_all_tax_rules(dataset, matches, cfg) that concatenates findings.

Tests (one file per module): positive, negative and decoy for every rule; duplicates keep the earliest; undercharge goes to REVIEW not NEEDS_FIX; cancelled supplier invoices dated before the cancellation are not flagged; rounding within 1 rupee auto-resolves.

Verify (paste output): pytest -q ; then run all tax rules on the seeded data and print counts by issue_type next to the ground_truth counts for the same types. They should be close; list any gaps and likely reasons.

Finish with the summary format from AGENTS.md.
```

---

## Stage 3b — Rules: 180-day clock, UPI fee, payments (0.6 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 3b: Payment-related rules. Folder you own: backend/app/rules/, backend/app/matching/payment_match.py (only the UPI hook) and backend/tests/.

Tasks:
1. rules/payment_clock.py: R-CLK-01 exactly as specified. Paid amount comes from matched payments (including batch payments). Compute unpaid_share, days_left, deadline. Warn when days_left <= PAYMENT_WARN_DAYS; negative days_left means REVERSE_ITC. Evidence must show invoice date, deadline, days left, paid and unpaid amounts, tax and the proportional amount at stake.
2. rules/upi_mdr.py: R-UPI-01. Implement mdr(amount, cfg) = min(round(amount * rate, 2), cap) applying only when channel is UPI, txn_kind is P2M, amount is strictly above the threshold, the date is on or after UPI_MDR_EFFECTIVE and the merchant is not exempt. Implement the real apply_upi_adjustment hook in matching/payment_match.py so that a credit equal to invoice total minus mdr (within tolerance) becomes match_type MDR_ADJUSTED. Produce UPI_MDR_ADJUSTED (AUTO_RESOLVED) findings with evidence like "invoice 3000, fee 12, deposit 2988".
3. In the same module, produce UPI_SHORT_SETTLEMENT_UNEXPLAINED for short UPI receipts not explained by the fee (including receipts before the effective date).
4. rules/payments.py: R-PAY-01 unmatched payments and unmatched receipts.
5. Update rules/__init__.py with run_all_payment_rules.

Tests: exactly ₹2,000 has no fee; ₹2,001 has a fee; ₹75,000 and above is capped at ₹300; ₹3,000 gives ₹12; a UPI receipt dated 2026-10-14 settled in full is clean; the same amount dated 2026-10-14 but short is UNEXPLAINED; exempt merchant flag turns the fee off; invoice exactly 180 days old unpaid gives days_left 0 and PAY_NOW; 181 days gives REVERSE_ITC; a partially paid invoice stakes only the unpaid share; a batch payment clears two invoices.

Verify (paste output): pytest -q ; print counts by issue_type for payment rules next to ground_truth counts.

Finish with the summary format from AGENTS.md.
```

---

## Stage 4 — Risk layer (1.25 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 4: Risk layer. Folder you own: backend/app/risk/ and backend/tests/.

Tasks:
1. risk/supplier_score.py: score_suppliers(dataset, findings, cycles) implementing BUSINESS_RULES section 5 exactly. Return per supplier: score 0 to 100, and factors as a list of {name, weight, normalised, contribution, plain_text}. Cancelled GSTIN gives 100 with the top factor "GSTIN cancelled".
2. risk/anomalies.py:
   a) detect_split_invoices implementing R-ANO-01 (rule based, one finding per group with all invoices in evidence).
   b) detect_statistical_anomalies implementing R-ANO-02 with IsolationForest (contamination 0.03, random_state from config) on the five features in BUSINESS_RULES. Skip invoices that already have any other finding. The plain reason must name the top contributing feature (compare the feature z-scores to pick one).
3. risk/graph.py: build a directed graph from trade_links with networkx, find simple cycles of length 3 to 5 with total value above the floor from BUSINESS_RULES, identify which of our suppliers are in cycles, and implement R-GRF-01 findings. Also return graph data for the API: nodes (id, label, is_our_supplier, in_cycle, score if available), edges (source, target, value) and cycles (list of node ids with total value). Wording must say "needs review", never "fraud".
4. risk/__init__.py: run_risk_layer(dataset, findings, cfg) -> RiskResult(supplier_scores, new_findings, graph).

Tests: score is 100 for cancelled suppliers; weights sum to 100; factor contributions sum to the score (except for cancelled); split detection catches 3 planted groups and ignores two invoices that are far apart in time; anomalies skip already-flagged invoices and are deterministic across runs; graph finds both planted cycles and no false cycles in a clean graph; cycles longer than 5 are ignored.

Verify (paste output): pytest -q ; print top 5 suppliers by score with their top 2 factors; print counts of split groups, anomalies, cycles vs ground truth.

Finish with the summary format from AGENTS.md.
```

---

## Stage 5 — Decision engine, pipeline, audit, evaluation (1.25 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 5: Turn findings into the ITC Recovery Queue and wire the real API. Folder you own: backend/app/decision/, backend/app/audit/, backend/app/eval/, backend/app/pipeline.py, backend/app/api/ (replace stubs for the endpoints listed below) and backend/tests/.

Tasks:
1. audit/chain.py: append_audit(session, actor, action, entity_type, entity_id, payload) with the hash chain from ARCHITECTURE section 10; verify_chain() returning {valid, broken_at_id}. Use canonical JSON (sorted keys, no spaces).
2. decision/priority.py: urgency multiplier, priority_score and severity exactly as ARCHITECTURE section 8. Bucket mapping as specified.
3. decision/issues.py: build_issues(findings, supplier_scores) creating Issue rows with title, plain_reason (use the fallback templates from BUSINESS_RULES section 7; implement them in llm/templates.py now as pure functions for every IssueType), recommended_action, deadline, days_left (computed from AS_OF_DATE), evidence_json. AUTO_RESOLVED items are stored but hidden from the default queue listing.
4. decision/liability.py: KPI buckets and liability maths exactly as ARCHITECTURE section 9, including the integrity equation. Per-invoice maximum rule so one invoice is never double counted.
5. record_status: write one status per source record (MATCHED, MATCHED_ADJUSTED, DISCREPANT, UNMATCHED, DUPLICATE).
6. pipeline.py: run_reconciliation(session, period) runs stages 1 to 5 in order, writes matches, findings to issues, supplier_scores, record_status, a recon_runs row, and audit rows (RUN_STARTED, RUN_COMPLETED with counts). Clear previous run outputs first so the run is idempotent.
7. eval/evaluate.py: compare issues to ground_truth and return precision, recall, and counts per IssueType plus overall; decoys flagged count as false positives.
8. Replace STUBS with real implementations for: POST /api/reconcile/run, GET /api/summary, GET /api/reconciliation/status, GET /api/reconciliation/records, GET /api/queue, GET /api/queue/{id}, PATCH /api/queue/{id} (audit row on each status change), GET /api/liability, GET /api/audit, GET /api/audit/verify, GET /api/evaluation. Keep response shapes identical to the schemas.

Tests: priority and severity table cases; KPI integrity equation on the seed data; queue sorted by priority_score descending; an invoice with two issues counts once in KPIs; PATCH writes an audit row and the chain verifies; tampering with an audit row's payload makes verify fail at the right id; pipeline is idempotent (two runs give the same counts); evaluation returns recall at least 0.9 and precision at least 0.85 for rule-based types, or report the gap precisely.

Verify (paste output): bash scripts/seed.sh ; curl -X POST http://localhost:8000/api/reconcile/run ; curl summary, top 5 queue items, evaluation ; pytest -q ; show the integrity equation numbers.

Finish with the summary format from AGENTS.md. If recall or precision is below target, list the 5 worst misses with the rule and cause; do not tune the rules to the ground truth.
```

Commit and tag `stage-5-done`. This is the milestone where the real numbers replace the stubs.

---

## Stage 6 — LLM layer and API completion (0.75 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 6: LLM layer and the remaining endpoints. Folder you own: backend/app/llm/, backend/app/api/, backend/tests/.

Tasks:
1. llm/client.py: a thin generate(prompt, system) function supporting LLM_PROVIDER = gemini | anthropic | none. Keys from environment only. 8 second timeout. Returns None on any failure or when provider is none.
2. llm/templates.py: confirm deterministic fallback text exists for every IssueType, plus vendor message drafts (subject and body) for these actions: CHASE_SUPPLIER, ASK_CREDIT_NOTE, REMOVE_DUPLICATE (internal note), PAY_NOW (internal reminder), HOLD_PAYMENT. Drafts must be polite, short, include invoice number, date, amount and the due date, and never accuse the supplier of fraud.
3. llm/service.py: explain_issue(issue) and draft_message(issue). Build the prompt from the structured issue JSON only. Instruct the model: plain language for a non-expert, 2 to 3 sentences, use only the numbers provided, do not give legal advice. After generation, validate that every rupee figure in the text appears in the input JSON; otherwise discard and use the template. Cache by prompt hash in llm_cache.
4. Endpoints: POST /api/queue/{id}/explain and POST /api/queue/{id}/draft store results on the issue and write audit rows EXPLANATION_GENERATED and DRAFT_GENERATED.
5. Replace remaining stubs: GET /api/suppliers, GET /api/suppliers/{id} (score, factors, open issues), GET /api/graph (from the latest run), GET /api/rules (rate table and active config), POST /api/data/upload/{kind} (CSV with schema validation, helpful errors, and a re-run hint). Mark upload as the first thing to drop if short on time.
6. Make sure /api/health reports as_of, period and the LLM provider.

Tests: with provider none the template is returned; a mocked model that invents a rupee figure is rejected and the template used; caching returns the same text without a second call; upload rejects a CSV with a missing column and names it; suppliers and graph endpoints match their schemas on real data.

Verify (paste output): pytest -q ; curl explain and draft for the top queue item with LLM_PROVIDER=none ; if a key is available, once with the provider on.

Finish with the summary format from AGENTS.md.
```

Commit and tag `stage-6-done`. Backend is complete.

---

## Stage 7a — Frontend scaffold and Dashboard (1 h)

Run in a second agent session as soon as Stage 0 is committed. It works against the stub API, then automatically against the real one.

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 7a: Frontend scaffold and the Dashboard page. Folder you own: frontend/ only. Do not edit backend/.

Tasks:
1. Scaffold frontend/ with Vite, React 18, TypeScript, Tailwind CSS, react-router, @tanstack/react-query, recharts, lucide-react, react-force-graph-2d, and vitest. VITE_API_URL defaults to http://localhost:8000/api.
2. src/styles/tokens.css: CSS variables, mapped in tailwind.config, using only these values. desk #FCFAF5, paper #F2E6CC, stain #D8BC8E, sepia #5A3A24, ink #231710, muted #6B5F55, risk #A3271F, maroon #6B1F2A, brass #B28A33. Plus radii, spacing and shadows. Shadows must be crisp and brown-tinted with no coloured glow. Safe has no colour; show it as ink text with a check icon. Brass is for fills only, never text on paper. Fonts: Playfair Display for titles, IBM Plex Sans (tabular numbers) for UI and tables, Kalam for notes. For charts in this stage use grayscale-and-brown fills with SVG hatch patterns; no coloured slices. Do not build the paper textures, floating symbols, book flip or equation loader yet; that is Stage 8.
3. src/api/: a typed client with one function per endpoint in ARCHITECTURE section 12 and TypeScript types mirroring backend/app/schemas.py (read that file). Wrap TanStack Query hooks (useSummary, useQueue, and so on).
4. src/lib/format.ts: formatINR (₹1,80,000 Indian grouping), formatLakh (₹6.8 L, ₹1.2 Cr), formatDate (18 Oct 2026), daysLeftLabel. Unit tests with vitest for edge cases (0, 999, 1,00,000, 1.5 crore, negative).
5. App shell: left nav or top nav with routes Dashboard, Recovery Queue, Reconciliation, Suppliers, Audit, Rules (only Dashboard implemented now; others show an EmptyState placeholder), a header with PeriodPicker (URL query param ?period=) and a footer with the disclaimer from ARCHITECTURE section 17.
6. Shared components: KpiCard, EmptyState, ErrorState (with retry), LoadingSkeleton, Badge (bucket and severity), Money.
7. Dashboard page: three KPI cards (Safe to claim, At risk, Needs a fix) with the exact colours from the tokens; a StatusDonut (matched, matched with adjustment, discrepant, unmatched, duplicate) with a source selector; a LiabilityPanel (output tax, ITC claimable now, net payable now, net payable if all issues are recovered, cash impact) with a one-line note on simplifications; a "Top 5 to act on" list showing amount, reason, deadline label and recommended action; an "Auto-matched" strip that shows rounding and UPI fee counts. Each KPI card links to the Queue page with the matching bucket filter.
8. Tooltips that explain ITC, GSTR-2B and At risk in one plain sentence each.

Verify (paste output): npm run build ; npm run test ; run the dev server with the backend running and describe what the Dashboard shows; take a screenshot with the browser tool if available and check there are no console errors.

Finish with the summary format from AGENTS.md.
```

## Stage 7b — Recovery Queue and issue drawer (1 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 7b: The Recovery Queue page and the issue drawer. Folder you own: frontend/ only.

Tasks:
1. Queue page: table with columns Priority rank, Supplier and issue (title, invoice number, date), Rupees at stake (formatINR, bold), Deadline (date plus days-left badge: red at 7 days or fewer, orange at 15 or fewer), Action (a coloured chip using the recommended_action label in plain words: "Chase supplier", "Pay now", "Ask for credit note", and so on), Status.
2. Filters in the URL query: bucket (default AT_RISK and NEEDS_FIX), issue type, severity, status, period, search by supplier or invoice. Sort by priority (default) or amount or deadline. Pagination.
3. IssueDrawer (opens on row click, route /queue/:id so it is linkable): header with severity and bucket badges; the plain-language reason; an Evidence table (label, value, source); "Why we flagged this" showing the rule id and the numbers; buttons: Explain this (calls POST explain and shows the text), Draft message (calls draft and shows subject and body with a Copy button), status buttons (Mark actioned, Mark resolved, Dismiss) with optimistic updates and error rollback; a link to the supplier.
4. Show the selected issue's supplier risk score and top factor in the drawer.
5. A sticky summary row above the table: count and total rupees for the current filter.
6. Keyboard: arrow keys move between rows, Enter opens the drawer, Esc closes it.
7. Empty state ("Nothing needs attention for this filter") and error state with retry.

Verify (paste output): npm run build ; npm run test ; walk through: open the queue, filter to AT_RISK, open the top item, generate an explanation and a draft, mark actioned, reload and confirm the status persists. Report any console errors.

Finish with the summary format from AGENTS.md.
```

## Stage 7c — Explorer, Suppliers, Audit, Rules pages (0.75 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 7c: Remaining pages. Folder you own: frontend/ only.

Tasks:
1. Reconciliation Explorer (/reconciliation): tabs for sources (Purchase books, GSTR-2B, Supplier invoices, Sales invoices, Bank), a status filter chip row with counts (Matched, Matched with adjustment, Discrepant, Unmatched, Duplicate), and a paged table of records. Each row shows its matched counterpart summary and the differences found (for example "tax differs by ₹1,200"). Clicking a discrepant row links to the related queue item.
2. Suppliers (/suppliers): table sorted by risk score with a score bar and the top factor in words; a detail drawer showing the five factors with contribution bars, the supplier's open issues and filing history. Network view: react-force-graph-2d with our suppliers highlighted, cycle nodes and edges in the risk colour, a visible label "Simulated counterparty network", and a side list of cycles with total value and the text "needs review". If time is short, ship the table and drawer first and the graph last.
3. Audit (/audit): list of audit rows (time, actor, action, entity), a "Verify chain" button showing valid or the id where it breaks, and an EvalCard showing precision and recall per issue type with the caption "measured on planted synthetic errors".
4. Rules and data (/rules): the rate table with before and after columns and the 22 Sep 2025 note, the active config values, and two buttons: "Regenerate sample data" and "Run reconciliation" with progress and a result toast. Confirm dialog before regenerating.
5. All pages: loading, empty and error states; no hard-coded colours.

Verify (paste output): npm run build ; npm run test ; click through every page with the backend running and report anything broken.

Finish with the summary format from AGENTS.md.
```

Commit and tag `stage-7-done`.

---

## Stage 8 — Apply the design template (1 h)

Wait until you have the design template. Paste its details (screenshots, Figma export, colours, fonts, spacing, component notes) into `docs/DESIGN.md` first, or attach them to the prompt.

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md and @docs/ARCHITECTURE.md. Follow them strictly. Do only the stage described below.

STAGE 8: Apply the design template. Folder you own: frontend/ only. This is a visual task. Do not change data logic, API calls, routes, or component props that other components depend on.

Design source: @docs/DESIGN.md and the attached images or files: [ATTACH OR DESCRIBE THE DESIGN HERE]

Tasks:
1. Read the design and write a short mapping table: design element to token to component. Show it to me before changing code.
2. Update src/styles/tokens.css and tailwind.config to the design's colours, fonts (load them with @fontsource or a Google Fonts link), radii, shadows, and spacing scale.
3. Restyle the app shell, KpiCard, Badge, QueueTable, IssueDrawer, StatusDonut, LiabilityPanel, SupplierTable, NetworkGraph, AuditList and EvalCard to match the design. Layouts may change; behaviour must not.
4. Keep colour meaning: green safe, maroon at risk, orange needs fix, neutral review. Do not rely on colour alone.
5. Check contrast (WCAG AA for body text), focus states, and a 1280 px wide laptop layout. Add a subtle page transition and skeleton loaders if the design calls for them.
6. Do not add new libraries unless the design cannot be built without them, and ask first.

Verify (paste output): npm run build ; npm run test ; screenshots of Dashboard, Queue with the drawer open, Suppliers, and Audit; list every place where the implementation differs from the design and why.

Finish with the summary format from AGENTS.md.
```

---

## Stage 9 — Integration, demo script, README (0.75 h)

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. Do only the stage described below.

STAGE 9: Integration, polish and demo readiness. Folders: both. No new features.

Tasks:
1. scripts/run_all.sh: one command that creates the venv if needed, installs backend and frontend dependencies, seeds data, runs the pipeline, then starts the backend and the frontend. Document it.
2. Run the full success checklist from PRD section 9 (SC-1 to SC-8). Report pass or fail for each with evidence. Fix failures with the smallest possible change.
3. Offline check: with LLM_PROVIDER=none and no internet, the whole demo flow works.
4. Reliability: handle backend unreachable (friendly banner with retry), empty database (prompt to seed), and a failed run (error with details in the UI).
5. Tamper demo: add a small script scripts/tamper_demo.py that edits one audit row in the DB so the verify button turns red, plus a restore step.
6. Write README.md: what it is, screenshots placeholder, quick start, architecture summary with the diagram, how detection accuracy is measured, assumptions and disclaimer, project structure, and a troubleshooting section.
7. Write docs/DEMO_SCRIPT.md: a 3-minute demo script with exact clicks and the sentence to say at each step. Flow: (a) the problem in one sentence, (b) Dashboard KPIs and liability, (c) Queue top item and drawer evidence, (d) explain and draft, (e) the 22 Sep 2025 rate case and the decoy that is correctly not flagged, (f) UPI fee explained deposit, (g) 180-day item, (h) supplier loop view, (i) audit verify and tamper, (j) evaluation card. Add a 1-minute version and a list of likely judge questions with short honest answers (synthetic data, accuracy scope, what is simulated, next steps).
8. Add a final lint and format pass (ruff or black for Python, eslint and prettier for the frontend) with no behaviour change.

Verify (paste output): bash scripts/run_all.sh on a clean clone; pytest -q; npm run build; the checklist table.

Finish with the summary format from AGENTS.md.
```

Commit and tag `final`. Keep a copy of `backend/data/itc_shield.db` as the demo fallback.

---

## Stage S — Stretch: invoice image reader (1 h)

Only if everything above is green with time to spare.

```text
You are working on ITC Shield. Before doing anything, read @AGENTS.md, @docs/PRD.md, @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. Follow them strictly. This is the optional stretch FR-4.

STAGE S: Invoice image reader. Folders: backend/app/ingest/ocr.py, backend/app/api/ (one endpoint), frontend/ (one small upload panel on the Rules and data page).

Tasks:
1. POST /api/ocr/invoice accepts a PNG, JPG or PDF. Use a vision-capable model through the existing llm client to extract: supplier name, supplier GSTIN, invoice number, invoice date, HSN or SAC, taxable value, tax rate, CGST, SGST, IGST, total. Return JSON with a confidence per field and an "ambiguous" flag where a value looks unclear or fails validation (invalid GSTIN format, tax parts not summing to the total within tolerance, date unreadable).
2. Never write to the database without user confirmation: the UI shows the extracted fields, highlights ambiguous ones in the risk colour, lets the user edit, then confirms. On confirm, insert into supplier_invoices with source_file set, write an audit row, and offer to re-run reconciliation.
3. Provide 4 sample invoice images under backend/data/samples/ (generate them with Pillow from synthetic data, one with a deliberately wrong rate and one with an unclear date) so the demo works offline of any real documents.
4. With LLM_PROVIDER=none, the endpoint returns a clear 503 message and the UI hides the feature.

Tests: validators (GSTIN format, tax sum, date parsing) with unit tests; the endpoint with a mocked model response.

Verify (paste output): pytest -q ; run the flow on a sample image and describe the result.

Finish with the summary format from AGENTS.md.
```

---

## Reusable prompts

### Stage checkpoint (run after every stage)

```text
Read @AGENTS.md. Review the work done in this stage against @docs/ARCHITECTURE.md and @docs/BUSINESS_RULES.md. List: (1) any renamed or changed contracts, (2) any hard-coded thresholds or dates, (3) any use of datetime.now, (4) tests that are missing for positive, negative and decoy cases, (5) anything in the code that reads ground_truth outside eval/. Fix problems of type 1 to 5 with the smallest change and show the diff summary. Then run the stage verify commands again and paste the output.
```

### Bug report

```text
Read @AGENTS.md. Bug: [what I did] -> [what happened] -> [what I expected]. First, reproduce it with a failing test or a curl command and show me the output. Then find the root cause and state it in two sentences before changing code. Fix with the smallest change, keep all existing tests passing, and add a regression test.
```

### "Show me the evidence" (when a number looks wrong)

```text
Read @AGENTS.md. For issue id [N] (or invoice [X]), list every record and every rule input that produced its amount_at_stake and priority_score, step by step with the formula and numbers. Do not change code. Tell me whether the result matches @docs/BUSINESS_RULES.md and, if not, which line differs.
```

### Scope guard (if the agent starts adding things)

```text
Stop. You added or proposed things outside this stage. Re-read the stage prompt and @AGENTS.md. Revert anything not required for this stage, list what you reverted, and continue with only the listed tasks.
```

---

## Hour-by-hour plan (about 11 hours)

| Hour | Session A (backend) | Session B (frontend) |
|---|---|---|
| 0.0 to 0.5 | Stage 0 | wait, then start 7a |
| 0.5 to 1.75 | Stage 1 | Stage 7a |
| 1.75 to 3.5 | Stage 2 | Stage 7b |
| 3.5 to 5.0 | Stage 3a, 3b | Stage 7c |
| 5.0 to 6.25 | Stage 4 | polish, empty and error states, wait for design |
| 6.25 to 7.5 | Stage 5 | Stage 8 when DESIGN.md is ready |
| 7.5 to 8.25 | Stage 6 | Stage 8 continues |
| 8.25 to 9.0 | wire frontend to real data, fix contract gaps | |
| 9.0 to 9.75 | Stage 9 | |
| 9.75 to 11.0 | buffer, rehearsal, optional Stage S | |