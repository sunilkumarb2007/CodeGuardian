from sqlalchemy.orm import Session
from uuid import UUID
import uuid
import logging
from datetime import datetime

from app.db import models
from app.db.repositories import MemoryRepository, IncidentRepository, TraceRepository
from app.schemas.memory import MemoryMatchResponse, FailureMemoryResponse, MemorySearchResponse
from app.engine.memory_engine import MemoryEngine

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)
        self.incident_repo = IncidentRepository(db)
        self.trace_repo = TraceRepository(db)
        self.engine = MemoryEngine()

    def search_memory_for_incident(self, incident_id: UUID) -> MemorySearchResponse:
        logger.info(f"Memory search started for incident {incident_id}")
        
        incident = self.incident_repo.get_by_id(incident_id)
        if not incident:
            return MemorySearchResponse(incident_id=incident_id, match_status="error")
            
        trace = self.trace_repo.get_by_incident_id(incident_id)
        
        # 1. Extract signature
        signature = self.engine.extract_signature(incident, trace)
        logger.info(f"Current failure signature extracted: {signature}")
        
        # 2. Get verified memories
        verified_memories = self.repo.get_verified_memories(incident.application_id)
        logger.info(f"Number of memories searched: {len(verified_memories)}")
        
        # 3. Match
        candidates = self.engine.match(signature, verified_memories)
        
        if not candidates:
            logger.info("No match found")
            return MemorySearchResponse(
                incident_id=incident_id,
                match_status="no_match",
                matches=[]
            )
            
        # 4. Save matches and prepare response
        matches = []
        for candidate in candidates:
            logger.info(f"Candidate match found: {candidate.memory.id}, Similarity score calculated: {candidate.similarity_score}")
            logger.info(f"Match reasons generated: {candidate.match_reasons}")
            
            match_record = models.MemoryMatch(
                id=uuid.uuid4(),
                incident_id=incident_id,
                memory_id=candidate.memory.id,
                similarity_score=candidate.similarity_score,
                match_reason=" | ".join(candidate.match_reasons),
                matched_error_pattern=candidate.matched_error_pattern,
                matched_root_cause=candidate.matched_root_cause,
                matched_affected_files=candidate.matched_affected_files,
                matched_code_context=False,
                verification_status="pending",
                created_at=datetime.utcnow()
            )
            
            match_record = self.repo.save_match(match_record)
            self.db.flush()
            
            # Map to response
            response_match = MemoryMatchResponse.model_validate(match_record)
            response_match.memory = FailureMemoryResponse.model_validate(candidate.memory)
            matches.append(response_match)
            
            logger.info("Memory match persisted. Adapted-fix candidate generated")
            
        self.db.commit()
        
        return MemorySearchResponse(
            incident_id=incident_id,
            match_status="match_found",
            matches=matches
        )

