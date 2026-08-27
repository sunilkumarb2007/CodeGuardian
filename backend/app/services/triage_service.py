from datetime import timezone
import logging
from uuid import UUID
from app.schemas.orchestration import TriageDecision

logger = logging.getLogger(__name__)

class TriageService:
    def triage_failure(self, repository_url: str, inspection_result=None, supplied_incident_id: UUID = None, db=None) -> TriageDecision:
        logger.info(f"Triaging failure for {repository_url}")
        
        # 1. If runtime evidence / incident is explicitly supplied
        if supplied_incident_id:
            logger.info("Found supplied incident ID. Route: supplied_failure")
            return TriageDecision(
                decision_type="supplied_failure",
                incident_id=supplied_incident_id,
                confidence=1.0
            )
            
        # 2. If static inspection detected a build/test failure
        if inspection_result and not inspection_result.static_analysis_passed:
            logger.info("Static inspection failed. Route: generic_defect")
            
            # Create a generic incident for this failure
            incident_id = None
            if db:
                from app.services.incident_service import IncidentService
                inc_svc = IncidentService(db)
                incident = inc_svc.create_incident({
                    "repository_url": repository_url,
                    "status": "investigating",
                    "failure_summary": inspection_result.failure_output[:500] if inspection_result.failure_output else "Unknown failure"
                })
                incident_id = incident.id
                
                # Attempt to parse stack trace
                import re
                stack_trace = None
                if inspection_result.failure_output:
                    # Look for typical Java stack trace lines e.g. at com.example.Class.method(Class.java:42)
                    java_trace_match = re.search(r'(at\s+[\w\.]+\.\w+\(\w+\.java:\d+\))', inspection_result.failure_output)
                    if java_trace_match:
                        # Grab a chunk of the stack trace
                        stack_trace_idx = inspection_result.failure_output.find(java_trace_match.group(1))
                        stack_trace = inspection_result.failure_output[max(0, stack_trace_idx-200):stack_trace_idx+1000]
                
                # Create an evidence event
                from app.db import models
                import uuid
                from datetime import datetime
                evidence = models.EvidenceEvent(
                    id=uuid.uuid4(),
                    incident_id=incident_id,
                    service_name="test_runner",
                    event_type="test",
                    timestamp=datetime.now(timezone.utc),
                    error_message=inspection_result.failure_output[:2000] if inspection_result.failure_output else "Unknown error",
                    stack_trace=stack_trace,
                    event_metadata=inspection_result.static_analysis_details if getattr(inspection_result, "static_analysis_details", None) else {"stdout": inspection_result.failure_output},
                    created_at=datetime.now(timezone.utc)
                )
                db.add(evidence)
                db.flush()

            return TriageDecision(
                decision_type="generic_defect",
                failure_summary=inspection_result.failure_output,
                incident_id=incident_id,
                confidence=0.9
            )
            
        # 3. Check for runtime telemetry / evidence in stdout even if static analysis passed
        if inspection_result and getattr(inspection_result, "static_analysis_details", None):
            stdout = inspection_result.static_analysis_details.get("stdout", "")
            import re
            # Look for common runtime error patterns in logs
            runtime_error_match = re.search(r'(error_code=[A-Z_]+|status_code=500|Exception:.*)', stdout)
            if runtime_error_match:
                logger.info("Runtime defect discovered in telemetry. Route: runtime_evidence")
                incident_id = None
                failure_summary = runtime_error_match.group(0)
                
                if db:
                    from app.services.incident_service import IncidentService
                    inc_svc = IncidentService(db)
                    incident = inc_svc.create_incident({
                        "repository_url": repository_url,
                        "status": "investigating",
                        "failure_summary": f"Runtime Error Detected: {failure_summary}"
                    })
                    incident_id = incident.id
                    
                    service_match = re.search(r'service=([^\s]+)', stdout)
                    svc_name = service_match.group(1) if service_match else "runtime_telemetry"
                    
                    stack_trace = None
                    java_trace_match = re.search(r'(at\s+[\w\.]+\.\w+\(\w+\.java:\d+\))', stdout)
                    if java_trace_match:
                        stack_trace_idx = stdout.find(java_trace_match.group(1))
                        stack_trace = stdout[max(0, stack_trace_idx-200):stack_trace_idx+1000]

                    from app.db import models
                    import uuid
                    from datetime import datetime
                    evidence = models.EvidenceEvent(
                        id=uuid.uuid4(),
                        incident_id=incident_id,
                        service_name=svc_name,
                        event_type="log",
                        timestamp=datetime.now(timezone.utc),
                        error_message=failure_summary,
                        stack_trace=stack_trace,
                        event_metadata=inspection_result.static_analysis_details,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(evidence)
                    db.flush()

                return TriageDecision(
                    decision_type="runtime_evidence",
                    failure_summary=f"Runtime Error Detected: {failure_summary}",
                    incident_id=incident_id,
                    confidence=0.95
                )

        # 4. No actionable defect found
        logger.info("No actionable defect detected. Route: no_actionable_defect")
        return TriageDecision(
            decision_type="no_actionable_defect",
            confidence=1.0
        )
