# HisabKitab (ITC Shield)
> Authenticated Vintage Ledger & GST Reconciliation Prototype built for Hackathon.

HisabKitab is an automated GST reconciliation platform designed to look like a vintage Indian "Bahi-Khata" ledger. It automatically flags risky suppliers, predicts 180-day ITC reversals, spots circular trading loops, and generates AI drafts for supplier communication.

## Quick Start (Judges)

The app is fully deployed!
* **Frontend:** `https://hisabkitab-green.vercel.app`
* **Backend API:** `https://hisabkitab-9lmf.onrender.com/api/health`

*(Note: The Render backend automatically fills its database with 520 synthetic invoices every time the server wakes up. If the data ever looks weird, simply go to the **Rules** tab in the app and click **Regenerate sample data**, followed by **Run reconciliation**!)*

## Running Locally

**1. Backend (FastAPI)**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Frontend (Vite/React)**
```bash
cd frontend
npm install
npm run dev
```

## Features
- **Deterministic Rule Engine:** Cross-references Purchase Books vs GSTR-2B.
- **Counterparty Network Graph:** Uses graph theory to highlight circular trading loops.
- **Simulated Tax Liability:** Calculates "Safe to Claim" vs "At Risk".
- **AI Fallback Architecture:** Designed to use LLMs for explaining discrepancies (currently running in fallback template mode to save tokens).
- **Tamper-Proof Audit Trail:** All actions are hashed and logged to simulate an immutable ledger.
