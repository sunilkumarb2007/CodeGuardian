from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import uuid

@dataclass
class NormalizedEvidence:
    id: str
    service_name: str
    event_type: str
    timestamp: datetime
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_error: bool = False
    
@dataclass
class TraceNode:
    id: str
    sequence_number: int
    service_name: str
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    node_type: str = "service"
    evidence_ids: List[str] = field(default_factory=list)

@dataclass
class TraceEdge:
    id: str
    from_node_id: str
    to_node_id: str
    relationship_type: str
    correlation_strength: float
    evidence_ids: List[str] = field(default_factory=list)

@dataclass
class TraceResult:
    trace_version: int
    symptom_service: Optional[str]
    root_cause_candidate: Optional[str]
    confidence: float
    reasoning_summary: str
    correlation_method: Dict[str, Any]
    nodes: List[TraceNode]
    edges: List[TraceEdge]
    status: str = "reconstructed" # reconstructed, partial, insufficient_evidence, conflicting_evidence
