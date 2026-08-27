from datetime import timezone
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
from app.engine.context_builder import InvestigationContextBuilder
from app.engine.context_builder import InvestigationContextBuilder
from app.engine.openrouter_investigator import OpenRouterInvestigator
from app.core.config import settings

logger = logging.getLogger(__name__)

class InvestigationService:
    def __init__(self, db=None):
        self.db = db
        self.openrouter_engine = OpenRouterInvestigator()

    def _emit_event(self, run_id: str | None, sequence: int, event_type: str, title: str, description: str):
        if not run_id:
            return
        ev = models.RunEvent(
            run_id=run_id,
            sequence=sequence,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            title=title,
            description=description,
            status="completed",
            related_entity_type="stage",
            related_entity_id="investigation"
        )
        if self.db:
            self.db.add(ev)
            self.db.commit()
        else:
            from app.db.database import SessionLocal
            with SessionLocal() as db:
                db.add(ev)
                db.commit()

    def investigate_incident(self, incident_id: str, attempt: int = 1, architecture: dict | None = None, run_id: str | None = None, deadline: float | None = None) -> InvestigationResult:
        logger.info(f"Starting investigation for incident {incident_id} (Attempt {attempt})")
        
        # 1. Gather Context
        def _get_context(db):
            incident_repo = IncidentRepository(db)
            evidence_repo = EvidenceRepository(db)
            trace_repo = TraceRepository(db)
            file_repo = RepositoryFileRepository(db)
            memory_service = MemoryService(db)

            inc_uuid = UUID(incident_id)
            incident = incident_repo.get_by_id(inc_uuid)
            if not incident:
                return InvestigationResult(incident_id=incident_id, status="error_incident_not_found")
                
            evidence = evidence_repo.get_by_incident_id(inc_uuid)
            trace = trace_repo.get_by_incident_id(inc_uuid)
            trace_id = trace.id if trace else None
            memory_response = memory_service.search_memory_for_incident(inc_uuid)
            
            if not trace:
                return InvestigationResult(incident_id=incident_id, status="error_trace_not_found")
                
            # 2. Select Source Files
            source_files = []
            all_files = []
            allowed_paths_precomputed = []
            if incident.repository_id:
                all_files = file_repo.get_files_by_repository_id(incident.repository_id)
                allowed_paths_precomputed = [f.file_path for f in all_files]
                source_files = InvestigationContextBuilder.extract_relevant_source_files(evidence, trace, all_files)
                if not source_files:
                    source_files = all_files[:10]
                    
            # Handle the placeholder scenario specifically mentioned in requirements
            if not source_files or all("placeholder" in (f.source_snapshot or "").lower() for f in source_files):
                return InvestigationResult(
                    incident_id=incident_id,
                    status="SOURCE_CONTEXT_UNAVAILABLE",
                    verification_requirements=["Source retrieval must be completed before patch generation."]
                )

            prompt = InvestigationPromptBuilder.build_prompt(
                incident=incident,
                evidence=evidence,
                trace=trace,
                memory_response=memory_response,
                source_files=source_files,
                architecture=architecture
            )
            return prompt, trace_id, allowed_paths_precomputed

        if self.db:
            context_res = _get_context(self.db)
        else:
            from app.db.database import SessionLocal
            with SessionLocal() as db:
                context_res = _get_context(db)
                
        if isinstance(context_res, InvestigationResult):
            return context_res
            
        prompt, trace_id, allowed_paths_precomputed = context_res

        self._emit_event(run_id, 301, "system", "Preparing investigation context", "Assembling evidence, architecture, and GhostTrace.")
        self._emit_event(run_id, 302, "analysis", "Loading historical memory matches", "Contextualizing failure with previous engineering knowledge.")
        self._emit_event(run_id, 303, "command", f"Opening relevant source files", "Isolating boundaries.")
        
        # 4. Invoke LLM
        engine = None
        if settings.openrouter_api_key:
            engine = self.openrouter_engine
            
        if not engine:
            self._emit_event(run_id, 304, "system", "Stub investigation started", "No AI provider configured.")
            return self._create_stub_result(incident_id, attempt)
            
        self._emit_event(run_id, 304, "system", f"{engine.provider_name.capitalize()} investigation started", "Sending bounded context to investigator.")
            
        if deadline is not None:
            import time
            if time.monotonic() >= deadline:
                return InvestigationResult(incident_id=incident_id, status="timeout")
            
        try:
            result = engine.investigate(prompt, deadline=deadline)
            if not result:
                return InvestigationResult(incident_id=incident_id, status="error_llm_failed")
        except RuntimeError as e:
            if "RATE_LIMIT" in str(e) or "QUOTA" in str(e):
                return InvestigationResult(incident_id=incident_id, status="RATE_LIMIT_EXCEEDED")
            if "INVESTIGATOR_NOT_CONFIGURED" in str(e):
                return self._create_stub_result(incident_id, attempt)
            if "INVESTIGATION_SCHEMA_ERROR" in str(e):
                return InvestigationResult(incident_id=incident_id, status="INVESTIGATION_SCHEMA_ERROR")
            if "INVESTIGATION_TIMEOUT" in str(e):
                return InvestigationResult(incident_id=incident_id, status="timeout")
            
            logger.error(f"OpenRouter investigation failed: {e}")
            return InvestigationResult(incident_id=incident_id, status="error_llm_failed")
            
        result.incident_id = incident_id
        result.status = "completed"
        
        self._emit_event(run_id, 305, "output", "Investigation response received", "Structured engineering analysis parsed.")
        if result.root_cause:
            self._emit_event(run_id, 306, "analysis", "Root cause identified", result.root_cause.summary)
        if result.repair_plan:
            self._emit_event(run_id, 307, "analysis", "Repair strategy generated", result.repair_plan.expected_behavior)
        if result.patch_candidate:
            allowed_paths = allowed_paths_precomputed
            for file in result.patch_candidate.files_changed:
                if ".." in file or file.startswith("/") or file.startswith("\\"):
                    logger.error(f"PATCH_PATH_UNSAFE: absolute or traversal paths not allowed: {file}")
                    return InvestigationResult(incident_id=incident_id, status="PATCH_PATH_UNSAFE")
                if file not in allowed_paths:
                    logger.error(f"PATCH_CONTEXT_INVALID: file not in repository: {file}")
                    return InvestigationResult(incident_id=incident_id, status="PATCH_CONTEXT_INVALID")
                    
            self._emit_event(run_id, 308, "system", "Patch candidate generated", f"Modified {len(result.patch_candidate.files_changed)} files.")
        
        # 5. Persist
        self._persist_investigation(incident_id, result, trace_id, attempt, engine=engine)
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

    def _persist_investigation(self, incident_id: UUID, result: InvestigationResult, trace_id: UUID | None, attempt: int = 1, engine=None):
        model_provider = engine.provider_name if engine else "stub"
        model_name = engine.model_name if engine else "stub"
        
        def _do_persist(db):
            inv_repo = InvestigationRepository(db)
            patch_repo = PatchRepository(db)
            
            inv_record = models.Investigation(
                id=uuid.uuid4(),
                incident_id=incident_id,
                failure_trace_id=trace_id,
                model_provider=model_provider,
                model_name=model_name,
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            inv_repo.save(inv_record)
            db.commit() # flush to generate ID if needed, though we set it
            
            if result.patch_candidate:
                from sqlalchemy.exc import IntegrityError
                
                max_retries = 3
                for retry_attempt in range(max_retries):
                    try:
                        # Safely determine patch_number
                        max_patch_number = patch_repo.get_max_patch_number(incident_id)
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
                            generated_by="openrouter",
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        patch_repo.save(patch_record)
                        db.commit()
                        break # Success
                    except IntegrityError as e:
                        db.rollback()
                        if retry_attempt < max_retries - 1:
                            logger.warning(f"IntegrityError inserting patch (likely concurrency on patch_number). Retrying {retry_attempt + 1}/{max_retries}")
                            continue
                        else:
                            logger.error(f"Failed to allocate patch number after {max_retries} attempts.")
                            raise e
            
                # Store the generated ID back to the result so the orchestrator can use it
                result.patch_candidate.id = patch_record.id

        if self.db:
            _do_persist(self.db)
        else:
            from app.db.database import SessionLocal
            with SessionLocal() as db:
                _do_persist(db)
