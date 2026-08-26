import uuid
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy.orm import Session

from app.db import models
from app.db.repositories import (
    IncidentRepository,
    EvidenceRepository,
    TraceRepository,
    RepositoryFileRepository,
    InvestigationRepository,
    PatchRepository,
)
from app.services.memory_service import MemoryService
from app.schemas.investigation import InvestigationResult
from app.engine.prompt_builder import InvestigationPromptBuilder
from app.engine.investigation_engine import InvestigationEngine

logger = logging.getLogger(__name__)

class InvestigationService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.trace_repo = TraceRepository(db)
        self.file_repo = RepositoryFileRepository(db)
        self.inv_repo = InvestigationRepository(db)
        self.patch_repo = PatchRepository(db)
        self.memory_service = MemoryService(db)
        self.engine = InvestigationEngine()

    def investigate_incident(self, incident_id: str, attempt: int = 1, architecture: dict | None = None) -> InvestigationResult:
        logger.info(f"Starting investigation for incident {incident_id} (Attempt {attempt})")
        
        # 1. Gather Context
        incident = self.incident_repo.get_by_id(UUID(incident_id))
        if not incident:
            return InvestigationResult(incident_id=incident_id, status="error_incident_not_found")
            
        evidence = self.evidence_repo.get_by_incident_id(incident_id)
        trace = self.trace_repo.get_by_incident_id(incident_id)
        memory_response = self.memory_service.search_memory_for_incident(incident_id)
        
        if not trace:
            return InvestigationResult(incident_id=incident_id, status="error_trace_not_found")
            
        # 2. Select Source Files
        source_files = []
        if incident.repository_id:
            all_files = self.file_repo.get_files_by_repository_id(incident.repository_id)
            # 1. Filter by stack trace in evidence
            for e in evidence:
                if e.stack_trace:
                    import re
                    # Example matcher for Java stack trace: at com.example.Class.method(Class.java:42)
                    java_trace_match = re.search(r'\(([\w\.]+\.java):\d+\)', e.stack_trace)
                    if java_trace_match:
                        file_name = java_trace_match.group(1)
                        source_files.extend([f for f in all_files if f.file_path.endswith(file_name)])
            
            # 2. Filter by trace root cause candidate if no stack trace match
            if not source_files and trace.root_cause_candidate:
                source_files = [f for f in all_files if trace.root_cause_candidate in f.file_path]
                
            if not source_files:
                source_files = all_files
                
        # Handle the placeholder scenario specifically mentioned in requirements
        if not source_files or all("placeholder" in (f.source_snapshot or "").lower() for f in source_files):
            return InvestigationResult(
                incident_id=incident_id,
                status="SOURCE_CONTEXT_UNAVAILABLE",
                verification_requirements=["Source retrieval must be completed before patch generation."]
            )
            
        # 3. Build Prompt
        prompt = InvestigationPromptBuilder.build_prompt(
            incident=incident,
            evidence=evidence,
            trace=trace,
            memory_response=memory_response,
            source_files=source_files,
            architecture=architecture
        )
        
        # 4. Invoke LLM
        if not self.engine.client:
            # Stub mode for local testing if API key is not set
            return self._create_stub_result(incident_id, attempt)
            
        try:
            result = self.engine.investigate(prompt)
            if not result:
                return InvestigationResult(incident_id=incident_id, status="error_llm_failed")
        except RuntimeError as e:
            if "GEMINI_QUOTA_EXHAUSTED" in str(e):
                return InvestigationResult(incident_id=incident_id, status="GEMINI_QUOTA_EXHAUSTED")
            return InvestigationResult(incident_id=incident_id, status="error_llm_failed")
            
        result.incident_id = incident_id
        result.status = "completed"
        
        # 5. Persist
        self._persist_investigation(incident_id, result, trace, attempt)
        return result

    def _create_stub_result(self, incident_id: UUID, attempt: int = 1) -> InvestigationResult:
        logger.info(f"Using stub investigation result (Attempt {attempt})")
        from app.schemas.investigation import RootCauseAnalysis, HistoricalReference, PatchCandidateModel
        
        if attempt % 10 == 1:
            # Simulate Python patch mismatch
            result = InvestigationResult(
                incident_id=incident_id,
                status="completed",
                root_cause=RootCauseAnalysis(
                    service="payment-service",
                    summary="Payment service accessed an object before validating its existence",
                    affected_file="payment-service/src/payment_service.py"
                ),
                historical_reference=HistoricalReference(
                    found=True,
                    memory_status="verified",
                    applicability="reference_only"
                ),
                patch_candidate=PatchCandidateModel(
                    status="unvalidated",
                    files_changed=["payment-service/src/payment_service.py"],
                    diff="--- payment-service/src/payment_service.py\n+++ payment-service/src/payment_service.py\n@@ -10 +10 @@\n-    process(obj)\n+    if obj:\n+        process(obj)",
                    explanation="Added null validation before object access as per historical reference."
                ),
                verification_requirements=["Build the affected service", "Run tests", "Replay the original failure"]
            )
        else:
            # Simulate valid Java patch
            result = InvestigationResult(
                incident_id=incident_id,
                status="completed",
                root_cause=RootCauseAnalysis(
                    service="payment-service",
                    summary="NullPointerException when accessing payment record",
                    affected_file="payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java"
                ),
                historical_reference=HistoricalReference(
                    found=True,
                    memory_status="verified",
                    applicability="reference_only"
                ),
                patch_candidate=PatchCandidateModel(
                    status="unvalidated",
                    files_changed=["payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java", "payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java"],
                    diff="""--- payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java
+++ payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java
@@ -15,7 +15,10 @@
     public CheckoutResponse charge(CheckoutRequest request) {
         PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());
 
         // Intentional bug: the null dereference happens before validation.
-        if (paymentRecord.getAmount() <= 0) {
+        if (paymentRecord == null) {
+            return new CheckoutResponse("SUCCESS", "Checkout completed", null);
+        }
+        if (paymentRecord.getAmount() <= 0) {
             throw new IllegalStateException("Invalid demo amount");
         }
""",
                    explanation="Added null check to PaymentProcessingService.java to prevent NPE."
                ),
                verification_requirements=["Build the affected service", "Run tests", "Replay the original failure"]
            )
            
        self._persist_investigation(incident_id, result, None, attempt)
        return result

    def _persist_investigation(self, incident_id: UUID, result: InvestigationResult, trace: models.FailureTrace | None, attempt: int = 1):
        inv_record = models.Investigation(
            id=uuid.uuid4(),
            incident_id=incident_id,
            failure_trace_id=trace.id if trace else None,
            model_provider="google",
            model_name=self.engine.model if self.engine.client else "stub",
            investigation_type="source_level",
            root_cause=result.root_cause.summary if result.root_cause else None,
            explanation=result.patch_candidate.explanation if result.patch_candidate else None,
            affected_files=result.patch_candidate.files_changed if result.patch_candidate else [],
            affected_lines=[], # To be implemented via fine-grained parsing if needed
            proposed_fix=result.patch_candidate.diff if result.patch_candidate else None,
            evidence_summary=" | ".join(result.evidence_used),
            memory_used=(result.historical_reference is not None and result.historical_reference.found),
            confidence=None,
            status="completed", # DB constraint requires 'completed'
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.inv_repo.save(inv_record)
        self.db.flush() # flush to generate ID if needed, though we set it
        
        if result.patch_candidate:
            from sqlalchemy.exc import IntegrityError
            
            max_retries = 3
            for retry_attempt in range(max_retries):
                try:
                    # Safely determine patch_number
                    max_patch_number = self.patch_repo.get_max_patch_number(incident_id)
                    next_patch_number = max_patch_number + 1
        
                    patch_record = models.Patch(
                        id=uuid.uuid4(),
                        incident_id=incident_id,
                        investigation_id=inv_record.id,
                        patch_number=next_patch_number,
                        diff=result.patch_candidate.diff,
                        affected_files=result.patch_candidate.files_changed,
                        generation_reason=result.patch_candidate.explanation,
                        status="unvalidated",
                        generated_by="gemini",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.patch_repo.save(patch_record)
                    self.db.flush()
                    break # Success
                except IntegrityError as e:
                    self.db.rollback()
                    if retry_attempt < max_retries - 1:
                        logger.warning(f"IntegrityError inserting patch (likely concurrency on patch_number). Retrying {retry_attempt + 1}/{max_retries}")
                        continue
                    else:
                        logger.error(f"Failed to allocate patch number after {max_retries} attempts.")
                        raise e
        
            # Store the generated ID back to the result so the orchestrator can use it
            result.patch_candidate.id = patch_record.id
