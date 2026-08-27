from datetime import timezone
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
import logging
from datetime import datetime
import uuid
import logging

from app.db import models
from app.db.repositories import TraceRepository, EvidenceRepository
from app.schemas.trace import GhostTraceResponse, TraceNodeResponse, TraceEdgeResponse
from app.engine.ghosttrace_engine import GhostTraceEngine

logger = logging.getLogger(__name__)

class GhostTraceService:
    def __init__(self, db: Session):
        self.db = db
        self.trace_repo = TraceRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.engine = GhostTraceEngine()

    def get_trace_for_incident(self, incident_id: UUID) -> GhostTraceResponse | None:
        """
        Retrieves the existing trace. If no trace exists, it returns None.
        """
        trace = self.trace_repo.get_by_incident_id(incident_id)
        if not trace:
            return None
            
        nodes = self.trace_repo.get_nodes(trace.id)
        edges = self.trace_repo.get_edges(trace.id)
        
        response = GhostTraceResponse.model_validate(trace)
        response.nodes = [TraceNodeResponse.model_validate(n) for n in nodes]
        response.edges = [TraceEdgeResponse.model_validate(e) for e in edges]
        
        return response

    def rebuild_trace(self, incident_id: UUID) -> GhostTraceResponse:
        """
        Forces a deterministic reconstruction of the trace from evidence.
        """
        # 1. Retrieve evidence
        events = self.evidence_repo.get_by_incident_id(incident_id)
        
        # 2. Engine reconstruction
        trace_result = self.engine.reconstruct(events)
        
        # 3. Persistence
        # Check if trace already exists
        existing_trace = self.trace_repo.get_by_incident_id(incident_id)
        
        try:
            if existing_trace:
                # To cleanly rebuild, delete old nodes and edges.
                self.db.query(models.FailureTraceEdge).filter(models.FailureTraceEdge.failure_trace_id == existing_trace.id).delete()
                self.db.query(models.FailureTraceNode).filter(models.FailureTraceNode.failure_trace_id == existing_trace.id).delete()
                
                # Update trace record
                existing_trace.trace_version += 1
                existing_trace.symptom_service = trace_result.symptom_service
                existing_trace.root_cause_candidate = trace_result.root_cause_candidate
                existing_trace.confidence = trace_result.confidence
                existing_trace.reasoning_summary = trace_result.reasoning_summary
                existing_trace.correlation_method = trace_result.correlation_method
                trace_id = existing_trace.id
            else:
                trace_id = uuid.uuid4()
                new_trace = models.FailureTrace(
                    id=trace_id,
                    incident_id=incident_id,
                    trace_version=1,
                    symptom_service=trace_result.symptom_service,
                    root_cause_candidate=trace_result.root_cause_candidate,
                    confidence=trace_result.confidence,
                    reasoning_summary=trace_result.reasoning_summary,
                    correlation_method=trace_result.correlation_method,
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(new_trace)
                
            self.db.flush()
            
            # Save nodes
            for n in trace_result.nodes:
                db_node = models.FailureTraceNode(
                    id=uuid.UUID(n.id),
                    failure_trace_id=trace_id,
                    sequence_number=n.sequence_number,
                    service_name=n.service_name,
                    endpoint=n.endpoint,
                    status_code=n.status_code,
                    error_message=n.error_message,
                    node_type=n.node_type,
                    evidence_ids=[uuid.UUID(e_id) for e_id in n.evidence_ids],
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(db_node)
            self.db.flush()
                
            # Save edges
            for e in trace_result.edges:
                db_edge = models.FailureTraceEdge(
                    id=uuid.UUID(e.id),
                    failure_trace_id=trace_id,
                    from_node_id=uuid.UUID(e.from_node_id),
                    to_node_id=uuid.UUID(e.to_node_id),
                    relationship_type=e.relationship_type,
                    correlation_strength=e.correlation_strength,
                    evidence_ids=[uuid.UUID(e_id) for e_id in e.evidence_ids],
                    created_at=datetime.now(timezone.utc)
                )
                self.db.add(db_edge)
                
            self.db.commit()
            logger.info(f"Trace rebuilt and persisted for incident {incident_id}")
            self.db.flush()
            logger.info(f"Trace rebuilt for incident {incident_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to persist rebuilt trace: {e}")
            logger.error(f"Failed to rebuild trace: {e}")
            raise
            
        return self.get_trace_for_incident(incident_id)
