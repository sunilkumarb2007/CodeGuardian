import uuid
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from app.db import models

@dataclass
class FailureSignature:
    error_fingerprint: str | None
    symptom_service: str | None
    root_cause_service: str | None
    error_pattern: str | None

@dataclass
class MemoryMatchCandidate:
    memory: models.FailureMemory
    similarity_score: float
    match_reasons: List[str]
    matched_error_pattern: bool
    matched_root_cause: bool
    matched_affected_files: bool

class MemoryEngine:
    def __init__(self):
        # Configurable weights
        self.WEIGHT_FINGERPRINT = 0.4
        self.WEIGHT_ROOT_CAUSE = 0.3
        self.WEIGHT_SYMPTOM = 0.2
        self.WEIGHT_PATTERN = 0.1
        self.MIN_THRESHOLD = 0.4

    def extract_signature(self, incident: models.Incident, trace: models.FailureTrace | None) -> FailureSignature:
        return FailureSignature(
            error_fingerprint=incident.error_fingerprint,
            symptom_service=trace.symptom_service if trace else incident.symptom_service,
            root_cause_service=trace.root_cause_candidate if trace else incident.root_cause_service,
            error_pattern=incident.title  # simple fallback if nothing else
        )

    def match(self, signature: FailureSignature, verified_memories: List[models.FailureMemory]) -> List[MemoryMatchCandidate]:
        candidates = []
        for mem in verified_memories:
            score = 0.0
            reasons = []
            
            matched_error_pattern = False
            matched_root_cause = False
            matched_affected_files = False
            
            if signature.error_fingerprint and mem.error_fingerprint and signature.error_fingerprint.lower() == mem.error_fingerprint.lower():
                score += self.WEIGHT_FINGERPRINT
                reasons.append(f"Same error fingerprint: {mem.error_fingerprint}")
                matched_error_pattern = True
                
            if signature.root_cause_service:
                # We do a basic keyword check on root cause service (replace hyphens)
                rc_svc = signature.root_cause_service.lower().replace('-', ' ')
                if mem.root_cause and (signature.root_cause_service.lower() in mem.root_cause.lower() or rc_svc in mem.root_cause.lower()):
                    score += self.WEIGHT_ROOT_CAUSE
                    reasons.append(f"Same root-cause service: {signature.root_cause_service}")
                    matched_root_cause = True
                elif mem.searchable_text and (signature.root_cause_service.lower() in mem.searchable_text.lower() or rc_svc in mem.searchable_text.lower()):
                    score += self.WEIGHT_ROOT_CAUSE
                    reasons.append(f"Same root-cause service: {signature.root_cause_service}")
                    matched_root_cause = True
                    
            if signature.symptom_service:
                if mem.searchable_text and signature.symptom_service.lower() in mem.searchable_text.lower():
                    score += self.WEIGHT_SYMPTOM
                    reasons.append(f"Same symptom service: {signature.symptom_service}")
                    
            # Pattern matching
            if signature.error_pattern and mem.error_pattern:
                # A simplistic pattern match
                import string
                sig_pattern = signature.error_pattern.lower().translate(str.maketrans('', '', string.punctuation))
                mem_pattern = mem.error_pattern.lower().translate(str.maketrans('', '', string.punctuation))
                # Check for common keywords
                sig_words = set(sig_pattern.split())
                mem_words = set(mem_pattern.split())
                common = sig_words.intersection(mem_words)
                
                if len(common) > 0:
                    score += self.WEIGHT_PATTERN
                    reasons.append("Similar error pattern")
                    matched_error_pattern = True
                    
            # Cap score to 1.0
            score = min(score, 1.0)
            
            if score >= self.MIN_THRESHOLD:
                # Add some deterministic fallback reason if empty
                if not reasons:
                    reasons.append("General failure similarity")
                    
                candidates.append(MemoryMatchCandidate(
                    memory=mem,
                    similarity_score=round(score, 4),
                    match_reasons=reasons,
                    matched_error_pattern=matched_error_pattern,
                    matched_root_cause=matched_root_cause,
                    matched_affected_files=matched_affected_files
                ))
                
        # Sort by similarity score descending, then by id to ensure determinism
        candidates.sort(key=lambda c: (-c.similarity_score, str(c.memory.id)))
        return candidates
