from typing import List, Dict, Any
from app.engine.models import NormalizedEvidence
from collections import defaultdict

class Correlator:
    def __init__(self, time_window_seconds: float = 60.0):
        self.time_window_seconds = time_window_seconds

    def correlate(self, evidence_list: List[NormalizedEvidence]) -> Dict[str, Any]:
        """
        Group events by request_id and temporal proximity.
        Returns a dict containing:
        - groups: list of grouped NormalizedEvidence
        - edges: list of (from_evidence, to_evidence, strength) inferred relationships
        """
        if not evidence_list:
            return {"groups": [], "edges": []}
            
        # Sort by timestamp
        sorted_evidence = sorted(evidence_list, key=lambda e: e.timestamp)
        
        edges = []
        # Basic correlation by request_id
        req_groups = defaultdict(list)
        for ev in sorted_evidence:
            if ev.request_id:
                req_groups[ev.request_id].append(ev)
                
        for req_id, group in req_groups.items():
            if len(group) > 1:
                # Infer sequential flow within the same request
                for i in range(len(group) - 1):
                    # For a standard sync request, the earlier event *typically* caused the later event 
                    # OR the earlier event called the downstream service.
                    # Wait, if A calls B, A's log might be before or after B's log.
                    # Usually, Gateway -> Order -> Payment -> DB.
                    # Gateway starts -> Order starts -> Payment starts -> DB fails -> Payment fails -> Order fails -> Gateway fails.
                    # However, simple approach: just link them sequentially as a correlation graph.
                    edges.append({
                        "from": group[i],
                        "to": group[i+1],
                        "strength": 0.9,
                        "reason": "Same request_id"
                    })
                    
        # Temporal correlation for events without request_id, linking close errors
        errors = [e for e in sorted_evidence if e.is_error]
        for i in range(len(errors)):
            for j in range(i + 1, len(errors)):
                time_diff = (errors[j].timestamp - errors[i].timestamp).total_seconds()
                if abs(time_diff) <= self.time_window_seconds and errors[i].request_id != errors[j].request_id:
                    edges.append({
                        "from": errors[i],
                        "to": errors[j],
                        "strength": 0.5,
                        "reason": "Temporal proximity"
                    })
                    
        return {
            "groups": list(req_groups.values()),
            "edges": edges
        }
