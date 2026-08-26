import pytest
from unittest.mock import patch, MagicMock
from app.services.inspection_service import RepositoryInspectionService
from app.schemas.orchestration import ArchitectureSummary

@patch("app.services.inspection_service.RepositoryInspectionService._clone_repo")
@patch("app.services.inspection_service.subprocess.run")
@patch("app.services.inspection_service.os.path.exists")
def test_inspect_repository(mock_exists, mock_run, mock_clone):
    # Mock os.path.exists to simulate a Python project with requirements.txt
    def fake_exists(path):
        if "requirements.txt" in path:
            return True
        return False
        
    mock_exists.side_effect = fake_exists
    mock_run.return_value = MagicMock(returncode=0)
    mock_clone.return_value = None
    
    svc = RepositoryInspectionService(token="fake_token")
    result = svc.inspect_repository("https://github.com/fake/repo")
    
    assert result.repository_url == "https://github.com/fake/repo"
    assert "Python" in result.architecture.tech_stack
    assert result.architecture.build_system == "pip"
    assert result.architecture.test_framework == "pytest"
    assert result.static_analysis_passed is True

def test_triage_supplied_incident():
    from app.services.triage_service import TriageService
    import uuid
    
    svc = TriageService()
    test_id = uuid.uuid4()
    
    result = svc.triage_failure("https://github.com/fake/repo", supplied_incident_id=test_id)
    assert result.decision_type == "supplied_failure"
    assert result.incident_id == test_id
    assert result.confidence == 1.0

def test_triage_static_failure():
    from app.services.triage_service import TriageService
    from app.schemas.orchestration import InspectionResult, ArchitectureSummary
    
    svc = TriageService()
    
    arch = ArchitectureSummary(tech_stack=["Python"])
    inspection = InspectionResult(
        repository_url="https://github.com/fake/repo",
        architecture=arch,
        static_analysis_passed=False,
        build_passed=True,
        test_passed=False,
        failure_output="Pytest failed"
    )
    
    result = svc.triage_failure("https://github.com/fake/repo", inspection_result=inspection)
    assert result.decision_type == "generic_defect"
    assert result.failure_summary == "Pytest failed"
    
def test_triage_no_defect():
    from app.services.triage_service import TriageService
    from app.schemas.orchestration import InspectionResult, ArchitectureSummary
    
    svc = TriageService()
    
    arch = ArchitectureSummary(tech_stack=["Python"])
    inspection = InspectionResult(
        repository_url="https://github.com/fake/repo",
        architecture=arch,
        static_analysis_passed=True,
        build_passed=True,
        test_passed=True
    )
    
    result = svc.triage_failure("https://github.com/fake/repo", inspection_result=inspection)
    assert result.decision_type == "no_actionable_defect"

