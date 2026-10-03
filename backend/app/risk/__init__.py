from dataclasses import dataclass
from . import graph, anomalies, supplier_score

@dataclass
class RiskResult:
    supplier_scores: dict
    new_findings: list
    graph_data: graph.GraphData

def run_risk_layer(dataset, findings, cfg) -> RiskResult:
    new_findings = []
    
    # 1. Split invoices
    split_findings = anomalies.detect_split_invoices(dataset, cfg)
    new_findings.extend(split_findings)
    
    # 2. Graph
    graph_findings, graph_data = graph.run(dataset, findings + new_findings, cfg)
    new_findings.extend(graph_findings)
    
    # 3. Statistical anomalies (skip those already flagged)
    stat_findings = anomalies.detect_statistical_anomalies(dataset, findings + new_findings, cfg)
    new_findings.extend(stat_findings)
    
    # 4. Supplier score
    scores = supplier_score.score_suppliers(dataset, findings + new_findings, graph_data.cycles)
    
    # Inject scores into graph data
    for node in graph_data.nodes:
        if node['is_our_supplier']:
            # map GSTIN to id
            sup = dataset.suppliers[dataset.suppliers['gstin'] == node['id']]
            if not sup.empty:
                sup_id = sup.iloc[0]['id']
                if sup_id in scores:
                    node['score'] = scores[sup_id]['score']
                    
    return RiskResult(
        supplier_scores=scores,
        new_findings=new_findings,
        graph_data=graph_data
    )
