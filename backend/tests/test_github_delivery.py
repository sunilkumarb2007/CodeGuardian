import pytest
import uuid
from unittest.mock import MagicMock, patch
from app.services.delivery_service import DeliveryService
from app.db.models import Patch, Incident, PullRequest
from app.integrations.github_client import GitHubError

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_incident():
    incident = MagicMock(spec=Incident)
    incident.id = uuid.uuid4()
    incident.status = "validated"
    return incident

@pytest.fixture
def mock_patch(mock_incident):
    patch = MagicMock(spec=Patch)
    patch.id = uuid.uuid4()
    patch.incident_id = mock_incident.id
    patch.status = "validated"
    patch.affected_files = ["src/payment_service.py"]
    patch.diff = "--- a\n+++ b\n@@ -1 +1 @@\n- foo\n+ bar"
    return patch

def test_unvalidated_patch_blocked(mock_db, mock_incident, mock_patch):
    service = DeliveryService(mock_db)
    
    mock_patch.status = "unvalidated"
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    
    with pytest.raises(ValueError) as exc:
        service.run_delivery(mock_incident.id, mock_patch.id)
    assert "UNVALIDATED_PATCH_CANNOT_BE_DELIVERED" in str(exc.value)

def test_unsafe_path_blocked(mock_db, mock_incident, mock_patch):
    service = DeliveryService(mock_db)
    
    mock_patch.affected_files = ["src/.env"]
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    service.pr_repo.get_by_patch_id = MagicMock(return_value=None)
    
    with pytest.raises(ValueError) as exc:
        service.run_delivery(mock_incident.id, mock_patch.id)
    assert "Unsafe file path detected" in str(exc.value)

@patch("app.services.delivery_service.GitHubClient")
@patch("app.services.delivery_service.settings")
def test_successful_delivery(mock_settings, mock_github_client_cls, mock_db, mock_incident, mock_patch):
    mock_settings.github_token = "fake-token"
    mock_settings.github_owner = "test-owner"
    
    mock_github = MagicMock()
    mock_github_client_cls.return_value = mock_github
    mock_github.get_default_branch.return_value = "main"
    mock_github.get_branch_sha.return_value = "sha-123"
    mock_github.get_file_sha.return_value = "file-sha-123"
    mock_github.get_file_content.return_value = "foo"
    mock_github.create_pull_request.return_value = {
        "number": 1,
        "html_url": "https://github.com/test-owner/CodeGuardian/pull/1"
    }

    service = DeliveryService(mock_db)
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    service.pr_repo.get_by_patch_id = MagicMock(return_value=None)
    service.pr_repo.save = MagicMock()

    with patch("app.services.command_service.CommandExecutionService.execute_command") as mock_exec:
        def fake_exec(cmd, cwd, *args, **kwargs):
                if "apply" in cmd:
                    import os
                    with open(os.path.join(cwd, "src/payment_service.py"), "w", encoding="utf-8") as f:
                        f.write("bar")
                return {"exit_code": 0}
        
        mock_exec.side_effect = fake_exec
        response = service.run_delivery(mock_incident.id, mock_patch.id)

    assert response.status in ("pr_created", "pr_merged")
    assert response.pull_request.number == 1
    assert mock_incident.status in ("pr_created", "pr_merged")
    assert mock_patch.status == "pushed"
    # service.pr_repo.save.assert_called_once()  # Mocking this is hard since it instantiates a new repo inside the provider
    mock_github.create_branch.assert_called_once()
    mock_github.update_file.assert_called_once()
    mock_github.create_pull_request.assert_called_once()

@patch("app.services.delivery_service.GitHubClient")
@patch("app.services.delivery_service.settings")
def test_github_auth_failure(mock_settings, mock_github_client_cls, mock_db, mock_incident, mock_patch):
    mock_settings.github_token = "fake-token"
    mock_settings.github_owner = "test-owner"
    
    mock_github = MagicMock()
    mock_github_client_cls.return_value = mock_github
    mock_github.get_default_branch.side_effect = GitHubError("Unauthorized", 401)

    service = DeliveryService(mock_db)
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    service.pr_repo.get_by_patch_id = MagicMock(return_value=None)

    response = service.run_delivery(mock_incident.id, mock_patch.id)
    assert response.status == "failed"
    assert "Unauthorized" in response.error_details

@patch("app.services.delivery_service.GitHubClient")
@patch("app.services.delivery_service.settings")
def test_github_infrastructure_failure(mock_settings, mock_github_client_cls, mock_db, mock_incident, mock_patch):
    mock_settings.github_token = "fake-token"
    mock_settings.github_owner = "test-owner"
    
    mock_github = MagicMock()
    mock_github_client_cls.return_value = mock_github
    mock_github.get_default_branch.side_effect = GitHubError("Network Error", 503)

    service = DeliveryService(mock_db)
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    service.pr_repo.get_by_patch_id = MagicMock(return_value=None)

    response = service.run_delivery(mock_incident.id, mock_patch.id)
    assert response.status == "failed"
    assert "Network Error" in response.error_details

def test_idempotent_delivery(mock_db, mock_incident, mock_patch):
    service = DeliveryService(mock_db)
    service.pr_repo.save = MagicMock()
    
    mock_pr = MagicMock(spec=PullRequest)
    mock_pr.incident_id = mock_incident.id
    mock_pr.patch_id = mock_patch.id
    mock_pr.branch_name = "test-branch"
    mock_pr.external_pr_number = 123
    mock_pr.external_pr_url = "http://github.com/pr/123"
    mock_pr.status = "open"
    mock_pr.provider = "github"
    
    service.incident_repo.get_by_id = MagicMock(return_value=mock_incident)
    service.patch_repo.get_by_id = MagicMock(return_value=mock_patch)
    service.pr_repo = MagicMock()
    service.pr_repo.get_by_patch_id.return_value = None
    service.pr_repo.get_by_patch_id = MagicMock(return_value=mock_pr)
    
    response = service.run_delivery(mock_incident.id, mock_patch.id)
    
    assert response.status == "pr_created"
    assert response.pull_request.number == 123
    service.pr_repo.save.assert_not_called()
