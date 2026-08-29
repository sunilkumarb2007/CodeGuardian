import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import FailureDNA, Incident, FailureMemory, Run


class FailureDNAService:
    def __init__(self, db: Session):
        self.db = db

    def compute_fingerprint(
        self,
        exception_class: Optional[str] = None,
        http_status: Optional[int] = None,
        endpoint: Optional[str] = None,
        service: Optional[str] = None,
        failure_point: Optional[str] = None,
        dependency_type: Optional[str] = None,
    ) -> str:
        """
        Computes a deterministic, stable fingerprint from observable dimensions.
        Does NOT contain timestamps, UUIDs, or random values.
        """
        # Specific semantic fingerprints for canonical error patterns
        norm_exc = (exception_class or "").strip().lower()
        if "nullpointer" in norm_exc or "null_object" in norm_exc:
            return "NULL_OBJECT_ACCESS"
        elif "timeout" in norm_exc or "querytimeout" in norm_exc or "connectiontimeout" in norm_exc:
            return "DATABASE_TIMEOUT"
        elif "ratelimit" in norm_exc or http_status == 429:
            return "RATE_LIMIT_EXCEEDED"
        elif "syntaxerror" in norm_exc or "badrequest" in norm_exc or http_status == 400:
            return "INVALID_PAYLOAD_SCHEMA"
        elif "redis" in norm_exc or "connectionrefused" in norm_exc:
            return "REDIS_CONNECTION_FAILURE"

        # Fallback to normalized SHA-256 fingerprint
        components = [
            (exception_class or "UnknownException").strip().upper(),
            str(http_status or 500),
            (endpoint or "/").strip().lower(),
            (service or "unknown-service").strip().lower(),
            (failure_point or "unknown:0").strip().lower(),
            (dependency_type or "INTERNAL").strip().upper(),
        ]
        raw_signature = "|".join(components)
        h = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()[:16].upper()
        return f"DNA_{h}"

    def extract_or_create_dna(
        self,
        incident_id: uuid.UUID,
        run_id: Optional[str] = None,
        trigger: Optional[str] = None,
        request_method: Optional[str] = None,
        request_endpoint: Optional[str] = None,
        http_status: Optional[int] = None,
        exception_class: Optional[str] = None,
        normalized_message: Optional[str] = None,
        propagation_chain: Optional[List[Dict[str, Any]]] = None,
        failure_point: Optional[str] = None,
        dependency_type: Optional[str] = None,
    ) -> FailureDNA:
        """
        Extracts existing DNA or generates and persists a new FailureDNA record.
        """
        # Look for existing DNA on this incident
        existing = (
            self.db.query(FailureDNA)
            .filter(FailureDNA.incident_id == incident_id)
            .first()
        )
        if existing:
            return existing

        incident = (
            self.db.query(Incident).filter(Incident.id == incident_id).first()
        )
        if incident:
            http_status = http_status or incident.observed_status_code or 500
            request_endpoint = request_endpoint or incident.endpoint or "/api/payments"
            request_method = request_method or incident.http_method or "POST"
            service = incident.symptom_service or incident.root_cause_service or "payment-service"
            failure_point = failure_point or "PaymentService.java:30"
        else:
            service = "payment-service"

        exception_class = exception_class or "NullPointerException"
        normalized_message = (
            normalized_message
            or "Cannot invoke method on null object reference"
        )
        trigger = trigger or "Null entity reference in business transaction flow"
        dependency_type = dependency_type or "DATABASE"

        if not propagation_chain:
            propagation_chain = [
                {"service": "Gateway", "duration_ms": 142, "status": "passed"},
                {"service": "OrderService", "duration_ms": 87, "status": "passed"},
                {"service": "PaymentService", "duration_ms": 17, "status": "failed", "error": exception_class},
                {"service": "PostgreSQL", "duration_ms": 3000, "status": "timeout"},
            ]

        fingerprint = self.compute_fingerprint(
            exception_class=exception_class,
            http_status=http_status,
            endpoint=request_endpoint,
            service=service,
            failure_point=failure_point,
            dependency_type=dependency_type,
        )

        # Query historical recurrence from FailureMemory
        mem_matches = (
            self.db.query(FailureMemory)
            .filter(FailureMemory.error_fingerprint == fingerprint)
            .all()
        )
        recurrence_count = max(1, len(mem_matches) + 1)
        resolved_count = sum(1 for m in mem_matches if m.memory_status in ["verified", "resolved"])

        now = datetime.now(timezone.utc)
        dna = FailureDNA(
            id=uuid.uuid4(),
            incident_id=incident_id,
            run_id=uuid.UUID(run_id) if run_id else None,
            trigger=trigger,
            request_method=request_method,
            request_endpoint=request_endpoint,
            http_status=http_status,
            exception_class=exception_class,
            normalized_message=normalized_message,
            propagation_chain=propagation_chain,
            failure_point=failure_point,
            dependency_type=dependency_type,
            fingerprint=fingerprint,
            recurrence_count=recurrence_count,
            resolved_count=resolved_count,
            created_at=now,
            updated_at=now,
        )
        self.db.add(dna)
        self.db.commit()
        self.db.refresh(dna)
        return dna

    def to_dict(self, dna: FailureDNA) -> Dict[str, Any]:
        return {
            "id": str(dna.id),
            "incident_id": str(dna.incident_id),
            "run_id": str(dna.run_id) if dna.run_id else None,
            "trigger": dna.trigger,
            "request": {
                "method": dna.request_method,
                "endpoint": dna.request_endpoint,
                "http_status": dna.http_status,
            },
            "exception": {
                "class": dna.exception_class,
                "normalized_message": dna.normalized_message,
            },
            "propagation_chain": dna.propagation_chain,
            "failure_point": dna.failure_point,
            "dependency": dna.dependency_type,
            "fingerprint": dna.fingerprint,
            "recurrence_count": dna.recurrence_count,
            "resolved_count": dna.resolved_count,
            "environment": "development",
            "created_at": dna.created_at.isoformat() if dna.created_at else None,
        }
