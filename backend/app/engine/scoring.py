from typing import List, Dict, Tuple
from app.engine.models import NormalizedEvidence

class Scorer:
    def __init__(self):
        pass
        
    def score_candidates(self, evidence_list: List[NormalizedEvidence]) -> List[Tuple[NormalizedEvidence, float, List[str]]]:
        """
        Returns a list of tuples: (candidate, score, reasoning)
        """
        candidates = []
        errors = [e for e in evidence_list if e.is_error]
        
        for ev in errors:
            score = 0.0
            reasoning = []
            
            # 1. Explicit error severity
            if ev.error_code:
                score += 0.3
                reasoning.append(f"Contains explicit error code: {ev.error_code}")
                
            if ev.status_code and ev.status_code >= 500:
                score += 0.2
                reasoning.append(f"Server error status: {ev.status_code}")
                
            # 2. Downstream position
            # In a naive approach, if an error happens earlier in time, it might be the cause
            # of a later 500. So earlier errors get a higher score.
            # Gateway 500 is typically last. Database timeout is typically first.
            earlier_count = sum(1 for e in errors if e.timestamp > ev.timestamp)
            if earlier_count > 0:
                score += 0.4
                reasoning.append("Error precedes other upstream failures (downstream indicator)")
                
            # 3. Error specificity
            if ev.service_name and ev.service_name != "api-gateway":
                score += 0.1
                reasoning.append("Error occurred in an internal service rather than the gateway")
                
            # Normalization (cap at 0.99 for confidence)
            score = min(score, 0.99)
            
            candidates.append((ev, score, reasoning))
            
        # Sort descending by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
