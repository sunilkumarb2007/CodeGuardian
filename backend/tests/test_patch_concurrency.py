import pytest
import uuid
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from app.schemas.investigation import InvestigationResult, RootCauseAnalysis, HistoricalReference, PatchCandidateModel
from app.services.investigation_service import InvestigationService

@pytest.fixture
def mock_db():
    return MagicMock()

def test_patch_concurrency_integrity_error_recovery(mock_db):
    service = InvestigationService(mock_db)
    
    # Setup mocks
    service.incident_repo = MagicMock()
    service.evidence_repo = MagicMock()
    service.trace_repo = MagicMock()
    service.file_repo = MagicMock()
    service.inv_repo = MagicMock()
    service.patch_repo = MagicMock()
    service.memory_service = MagicMock()
    
    # Ensure get_max_patch_number works
    service.patch_repo.get_max_patch_number.side_effect = [1, 2] # Simulates it returning 1 first, then 2 on retry
    
    # We want save to fail once with IntegrityError, then succeed
    def mock_save(*args, **kwargs):
        if service.patch_repo.save.call_count == 1:
            raise IntegrityError("mock error", "mock params", "mock orig")
        return None
        
    service.patch_repo.save.side_effect = mock_save
    
    # Create fake result
    incident_id = uuid.uuid4()
    trace = MagicMock()
    trace.id = uuid.uuid4()
    
    result = InvestigationResult(
        incident_id=incident_id,
        status="completed",
        root_cause=RootCauseAnalysis(service="s", summary="sum", affected_file="f"),
        patch_candidate=PatchCandidateModel(
            status="unvalidated",
            files_changed=["file.py"],
            diff="fake diff",
            explanation="fake exp"
        )
    )
    
    # Run the function
    service._persist_investigation(incident_id, result, trace, attempt=1)
    
    # Verifications
    assert service.patch_repo.save.call_count == 2
    assert service.patch_repo.get_max_patch_number.call_count == 2
    assert mock_db.rollback.call_count == 1
    assert mock_db.flush.call_count == 2 # 1 for inv_repo.save, 1 for successful patch_repo.save

def test_patch_concurrency_failure_after_retries(mock_db):
    service = InvestigationService(mock_db)
    
    # Setup mocks
    service.incident_repo = MagicMock()
    service.inv_repo = MagicMock()
    service.patch_repo = MagicMock()
    
    service.patch_repo.get_max_patch_number.return_value = 1
    
    # Always fail
    service.patch_repo.save.side_effect = IntegrityError("mock error", "mock params", "mock orig")
    
    incident_id = uuid.uuid4()
    trace = MagicMock()
    trace.id = uuid.uuid4()
    
    result = InvestigationResult(
        incident_id=incident_id,
        status="completed",
        root_cause=RootCauseAnalysis(service="s", summary="sum", affected_file="f"),
        patch_candidate=PatchCandidateModel(
            status="unvalidated",
            files_changed=["file.py"],
            diff="fake diff",
            explanation="fake exp"
        )
    )
    
    # Expect it to raise IntegrityError after retries exhaust
    with pytest.raises(IntegrityError):
        service._persist_investigation(incident_id, result, trace, attempt=1)
        
    assert service.patch_repo.save.call_count == 3
    assert mock_db.rollback.call_count == 3
