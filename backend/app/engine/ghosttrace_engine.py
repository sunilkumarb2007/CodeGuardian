from typing import List, Dict, Any, Tuple
import uuid
import logging
from app.db import models
from app.engine.models import NormalizedEvidence, TraceResult, TraceNode, TraceEdge
from app.engine.correlation import Correlator
from app.engine.root_cause import classify_signal
from app.engine.scoring import Scorer
from app.engine.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)

class GhostTraceEngine:
    def __init__(self):
        self.correlator = Correlator(time_window_seconds=60.0)
        self.scorer = Scorer()
        self.graph_builder = GraphBuilder()
        
    def _normalize(self, events: List[models.EvidenceEvent]) -> List[NormalizedEvidence]:
        normalized = []
        for ev in events:
            norm_ev = NormalizedEvidence(
                id=str(ev.id),
                service_name=ev.service_name or "unknown",
                event_type=ev.event_type,
                timestamp=ev.timestamp,
                request_id=ev.request_id,
                endpoint=ev.endpoint,
                http_method=ev.http_method,
                status_code=ev.status_code,
                error_code=ev.error_code,
                error_message=ev.error_message
            )
            classify_signal(norm_ev)
            normalized.append(norm_ev)
        return normalized

    def reconstruct(self, evidence_events: List[models.EvidenceEvent]) -> TraceResult:
        logger.info(f"GhostTrace Engine started with {len(evidence_events)} events.")
        
        if not evidence_events:
            return TraceResult(
                trace_version=1,
                symptom_service=None,
                root_cause_candidate=None,
                confidence=0.0,
                reasoning_summary="Insufficient evidence to reconstruct a failure chain.",
                correlation_method={"method": "deterministic"},
                nodes=[],
                edges=[],
                status="insufficient_evidence"
            )
            
        # 1. Normalize
        normalized_evidence = self._normalize(evidence_events)
        
        # 2. Correlate
        correlation_result = self.correlator.correlate(normalized_evidence)
        logger.info("Correlation performed.")
        
        # 3. Graph Construction
        nodes, edges = self.graph_builder.build_graph(correlation_result)
        
        # 4. Root Cause Ranking
        candidates = self.scorer.score_candidates(normalized_evidence)
        logger.info(f"Candidate count: {len(candidates)}")
        
        if not candidates:
             return TraceResult(
                trace_version=1,
                symptom_service=None,
                root_cause_candidate=None,
                confidence=0.0,
                reasoning_summary="No explicit errors detected to determine root cause.",
                correlation_method={"method": "deterministic"},
                nodes=nodes,
                edges=edges,
                status="partial"
            )
            
        best_candidate, score, reasoning = candidates[0]
        
        # Find symptom (typically highest level 500 error, or gateway)
        symptom_ev = next((e for e in reversed(normalized_evidence) if e.is_error and e.service_name == "api-gateway"), None)
        if not symptom_ev:
            symptom_ev = next((e for e in reversed(normalized_evidence) if e.is_error), None)
            
        symptom_service = symptom_ev.service_name if symptom_ev else None
        
        reasoning_str = " | ".join(reasoning)
        logger.info(f"Root cause candidate selected: {best_candidate.service_name}")
        
        return TraceResult(
            trace_version=1,
            symptom_service=symptom_service,
            root_cause_candidate=best_candidate.service_name,
            confidence=score,
            reasoning_summary=reasoning_str,
            correlation_method={"method": "deterministic", "window": 60},
            nodes=nodes,
            edges=edges,
            status="reconstructed"
        )
