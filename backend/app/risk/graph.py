import networkx as nx
import pandas as pd
from app.rules.base import Finding, Evidence
from dataclasses import dataclass

@dataclass
class GraphData:
    nodes: list[dict]
    edges: list[dict]
    cycles: list[dict]

def run(dataset, findings_list, cfg):
    findings = []
    
    G = nx.DiGraph()
    
    # Identify our suppliers
    our_suppliers = {}
    for _, s in dataset.suppliers.iterrows():
        our_suppliers[s['gstin']] = s['id']
        
    edges_list = []
    for _, r in dataset.trade_links.iterrows():
        u = r['from_gstin']
        v = r['to_gstin']
        val = float(r['value'])
        
        if G.has_edge(u, v):
            G[u][v]['value'] += val
        else:
            G.add_edge(u, v, value=val)
            
    # Find cycles
    # simple_cycles can be many, we might need to restrict or filter
    all_cycles = list(nx.simple_cycles(G))
    
    valid_cycles = []
    nodes_in_cycle = set()
    
    for cycle in all_cycles:
        if 3 <= len(cycle) <= 5:
            # Calculate total value
            total_val = 0.0
            for i in range(len(cycle)):
                u = cycle[i]
                v = cycle[(i + 1) % len(cycle)]
                total_val += G[u][v]['value']
                
            if total_val >= 500000.0:
                valid_cycles.append({
                    "nodes": cycle,
                    "total_value": total_val
                })
                nodes_in_cycle.update(cycle)
                
                # Flag our suppliers in the cycle
                for node in cycle:
                    if node in our_suppliers:
                        sup_id = our_suppliers[node]
                        # Don't add duplicate findings per supplier
                        if not any(f.issue_type == 'CIRCULAR_TRADING' and f.supplier_id == sup_id for f in findings):
                            findings.append(Finding(
                                rule_id='R-GRF-01',
                                issue_type='CIRCULAR_TRADING',
                                entity_type='supplier',
                                entity_id=sup_id,
                                supplier_id=sup_id,
                                amount_at_stake=0.0,
                                confidence=0.6,
                                evidence=[
                                    Evidence('cycle_length', len(cycle), 'graph'),
                                    Evidence('cycle_value', total_val, 'computed')
                                ],
                                deadline=None,
                                action='INVESTIGATE',
                                bucket='REVIEW',
                                reason="part of a loop of invoices between the same firms; needs review"
                            ))
                            
    # Build graph data output
    nodes_out = []
    for node in G.nodes():
        nodes_out.append({
            "id": node,
            "label": node,
            "is_our_supplier": node in our_suppliers,
            "in_cycle": node in nodes_in_cycle
        })
        
    edges_out = []
    for u, v, d in G.edges(data=True):
        edges_out.append({
            "source": u,
            "target": v,
            "value": d['value']
        })
        
    return findings, GraphData(nodes=nodes_out, edges=edges_out, cycles=valid_cycles)
