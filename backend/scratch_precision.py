from sqlmodel import create_engine, Session, select
from app.pipeline import run_reconciliation
from app.config import config
from app.eval.evaluate import evaluate_run
import json

engine = create_engine('sqlite:///data/itc_shield.db')
with Session(engine) as session:
    res = evaluate_run(session, 1)
    print("Per-type metrics:")
    for t in ['AMOUNT_MISMATCH', 'MISSING_IN_GSTR2B', 'MISSING_IN_BOOKS', 'WRONG_TAX_RATE', 'PAYMENT_180_DAY_RISK', 'SPLIT_INVOICE']:
        if t in res['by_type']:
            m = res['by_type'][t]
            print(f"  {t}: precision={m['precision']}, recall={m['recall']}, tp={m['tp']}, pred={m['pred']}, gt={m['gt']}")
