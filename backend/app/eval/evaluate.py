import json
from sqlmodel import Session, select
from app.models import Issue, GroundTruth

def evaluate_run(session: Session, run_id: int):
    issues = session.exec(select(Issue).where(Issue.run_id == run_id)).all()
    ground_truths = session.exec(select(GroundTruth)).all()
    
    gt_map = {}
    gt_counts = {}
    for gt in ground_truths:
        gt_map[(gt.entity_type, str(gt.entity_id))] = gt.injected_issue_type
        if gt.injected_issue_type:
            gt_counts[gt.injected_issue_type] = gt_counts.get(gt.injected_issue_type, 0) + 1
            
    # For CIRCULAR_TRADING, GT has 'supplier' entity_type, and our issues have 'supplier' entity_type.
    # Wait, our issues for CIRCULAR_TRADING have entity_type 'supplier' and entity_id as supplier_id.
    
    tp_counts = {}
    pred_counts = {}
    
    for i in issues:
        t = i.issue_type
        pred_counts[t] = pred_counts.get(t, 0) + 1
        
        # Check match
        # Handle special cases where one issue maps to multiple GTs
        if t == 'SPLIT_INVOICE':
            # Evidence contains 'invoices' with comma-separated IDs
            evs = json.loads(i.evidence_json)
            inv_ids = []
            for ev in evs:
                if ev['label'] == 'invoices':
                    inv_ids = [x.strip() for x in str(ev['value']).split(',')]
            
            matched = 0
            for inv_id in inv_ids:
                if gt_map.get((i.entity_type, inv_id)) == t:
                    matched += 1
                    
            if matched > 0:
                # Add all matched to TP to align with GT counts
                tp_counts[t] = tp_counts.get(t, 0) + matched
                # We also increase pred_count by (matched - 1) because the issue covers multiple GTs
                pred_counts[t] += (matched - 1)
        elif t == 'CIRCULAR_TRADING':
            gt_type = gt_map.get((i.entity_type, str(i.entity_id)))
            if gt_type == t:
                tp_counts[t] = tp_counts.get(t, 0) + 1
        else:
            gt_type = gt_map.get((i.entity_type, str(i.entity_id)))
            if gt_type == t:
                tp_counts[t] = tp_counts.get(t, 0) + 1
                
    results = {}
    total_tp = 0
    total_pred = 0
    total_gt = 0
    
    all_types = set(gt_counts.keys()).union(set(pred_counts.keys()))
    
    for t in all_types:
        tp = tp_counts.get(t, 0)
        pred = pred_counts.get(t, 0)
        gt = gt_counts.get(t, 0)
        
        precision = tp / pred if pred > 0 else 1.0
        recall = tp / gt if gt > 0 else 1.0
        
        total_tp += tp
        total_pred += pred
        total_gt += gt
        
        results[t] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "tp": tp,
            "pred": pred,
            "gt": gt
        }
        
    overall_precision = total_tp / total_pred if total_pred > 0 else 1.0
    overall_recall = total_tp / total_gt if total_gt > 0 else 1.0
    
    return {
        "overall": {
            "precision": round(overall_precision, 3),
            "recall": round(overall_recall, 3),
            "tp": total_tp,
            "pred": total_pred,
            "gt": total_gt
        },
        "by_type": results
    }
