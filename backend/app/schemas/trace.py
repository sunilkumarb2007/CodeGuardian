from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class TraceNodeResponse(BaseModel):
    id: UUID
    sequence_number: int
    service_name: str
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    node_type: Optional[str] = None
    evidence_ids: Optional[List[UUID]] = None

    model_config = ConfigDict(from_attributes=True)

class TraceEdgeResponse(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    relationship_type: str
    correlation_strength: Optional[float] = None
    evidence_ids: Optional[List[UUID]] = None

    model_config = ConfigDict(from_attributes=True)

class GhostTraceResponse(BaseModel):
    id: UUID
    incident_id: UUID
    trace_version: int
    symptom_service: Optional[str] = None
    root_cause_candidate: Optional[str] = None
    confidence: Optional[float] = None
    reasoning_summary: Optional[str] = None
    nodes: List[TraceNodeResponse] = []
    edges: List[TraceEdgeResponse] = []

    model_config = ConfigDict(from_attributes=True)
