# PART 1 — Paste into AGENTS.md

## Project

HisabKitab: a pre-filing GST reconciliation web app for a hackathon prototype (team Fintastic). Backend: Python 3.11, FastAPI, SQLModel, SQLite, pandas, RapidFuzz, scikit-learn, NetworkX. Frontend: React 18, Vite, TypeScript, Tailwind, TanStack Query, Recharts.

Read before working: @docs/PRD.md, @docs/ARCHITECTURE.md, @docs/BUSINESS_RULES.md. If a task conflicts with them, stop and ask instead of improvising.

## Source of truth order

1. `docs/BUSINESS_RULES.md` for tax and detection logic, thresholds, formulas, data spec.
2. `docs/ARCHITECTURE.md` for structure, schemas, API, contracts.
3. `docs/PRD.md` for scope and priorities.
4. The prompt you were just given.
If two disagree, follow the earlier one and say so in your summary.

## Scope discipline

- Do only what the current stage prompt asks. No extra features, pages, libraries or refactors.
- Do not touch files outside the folders named in the prompt. If you must, say why first.
- Do not add dependencies that are not in ARCHITECTURE section 3 without asking.
- Stretch features (invoice image reader) are off unless the prompt says so.
- Never rename enums, tables, endpoints or JSON fields defined in ARCHITECTURE. The frontend depends on them.

## Determinism and correctness

- Never call `datetime.now()` or `date.today()` in business logic. Use `config.AS_OF_DATE`.
- Seed every random source with `config.RANDOM_SEED`. Same seed and as-of date must give identical output.
- Money is float rounded to 2 decimals. Compare with `config.ROUNDING_TOLERANCE`, never with `==`.
- Every threshold, rate and date comes from config or the rate table. No magic numbers in rule code.
- Rule code must never read `ground_truth`. Only `eval/` may.
- Each finding stores `rule_id`, inputs and computed numbers in `evidence`, so the UI can show the working.
- Do not invent tax law. If a rule is unclear, implement what BUSINESS_RULES says and leave a `TODO(verify)` comment.

## Python style

- Type hints on all functions. Pydantic v2 for schemas, SQLModel for tables.
- Small pure functions that take data and config and return dataclasses. No hidden globals.
- Modules are named as in ARCHITECTURE section 4. Keep files under about 300 lines; split by responsibility.
- Use `logging`, not `print`. No bare `except`.
- Public functions get a one-line docstring saying what and why.

## Testing

- Write pytest tests with the code, not after. Each rule needs a positive case, a negative case and a decoy.
- Before saying a stage is done: run `pytest -q` from `backend/` and the stage's verify commands. Paste the real output in your summary. Do not claim success without running them.
- Do not weaken or delete a failing test to make it pass. Fix the code, or report the conflict.
- Keep tests fast (whole suite under 30 seconds).

## API rules

- Every endpoint is under `/api`, returns JSON, uses the schemas in `app/schemas.py` and appears in OpenAPI.
- Errors return `{"error": {"code": str, "message": str}}` with the right status code.
- List endpoints are paginated (`page`, `page_size`, default 50) except where ARCHITECTURE says otherwise.
- Writes that change state (status change, seed, run) must append an audit row.

## LLM rules

- The app must work with `LLM_PROVIDER=none`. Template fallback is mandatory.
- The model only phrases facts. It receives structured issue JSON and never computes amounts.
- Validate generated text: every rupee figure must appear in the input JSON, else discard and use the template.
- Timeout 8 seconds. Cache by prompt hash. Never log API keys. Keys come from `.env` only.

## Frontend rules
- Colour rule: never use orange, navy blue, purple or green, and no glow effects (no coloured or blurred glows, neon, shine gradients). Colour is reserved for exceptions: safe = plain ink with a check mark, at risk = sindoor red, needs fix = brass fill with dark text, review = grey.
- Use only the routes and components in ARCHITECTURE section 13.
- No hard-coded colours, radii or fonts in components. Use design tokens in `src/styles/tokens.css` through Tailwind.
- All server data goes through one typed API client in `src/api/`. Types mirror `schemas.py`.
- Every data view needs loading, empty and error states.
- Indian number format for money (`₹1,80,000`) via one shared helper, and lakh shorthand (`₹6.8 L`) on KPI cards.
- Accessible by default: semantic HTML, button labels, colour never the only signal (add icon or text).
- Plain-language copy. Use the glossary words from BUSINESS_RULES section 1.
- Until `docs/DESIGN.md` exists, use the neutral warm theme from the PRD. Do not invent a brand.

## Security and hygiene

- No real personal or company data. All names, GSTINs and numbers are synthetic.
- Secrets only in `.env` (gitignored). Commit `.env.example`.
- CORS: allow only the Vite dev origin.
- Do not run destructive commands (`rm -rf` outside `backend/data` or `node_modules`, force pushes, dropping files you did not create).

## Working style

- For each task: plan first (short), then implement, then verify, then summarise.
- Keep commits small, one per sub-task, message format `stageN: what changed`.
- End every task with a summary containing: files created or changed, how to run, verify output, assumptions made, deviations from the docs, open questions.
- If blocked or if something takes more than about 20 minutes of trial and error, stop and report instead of guessing.
- Prefer boring, readable code over clever code. This is a demo that must not fail on stage.

## Definition of done (any stage)

1. Code matches the docs, with no renamed contracts.
2. Tests written and passing, output pasted.
3. Verify commands from the prompt were run, output pasted.
4. No `TODO` left except `TODO(verify)` on tax-law assumptions.
5. Summary delivered in the required format.