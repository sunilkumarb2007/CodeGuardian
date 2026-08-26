import pytest
import uuid
import base64
from unittest.mock import MagicMock, patch
from app.services.delivery_service import DeliveryService
from app.integrations.github_client import GitHubError
from app.schemas.github import PullRequestDeliveryResponse

@pytest.fixture
def mock_db():
    return MagicMock()

def test_delivery_fetches_original_and_applies_diff(mock_db):
    service = DeliveryService(mock_db)
    
    # Mocks
    service.incident_repo = MagicMock()
    service.patch_repo = MagicMock()
    service.pr_repo = MagicMock()
    service.github_client = MagicMock()
    
    incident = MagicMock()
    incident.id = uuid.uuid4()
    incident.repository_url = "https://github.com/sunilkumarb2007/JavaAPICheck"
    service.incident_repo.get_by_id.return_value = incident
    
    patch_obj = MagicMock()
    patch_obj.id = uuid.uuid4()
    patch_obj.incident_id = incident.id
    patch_obj.status = "validated"
    patch_obj.affected_files = ["src/test.java"]
    patch_obj.diff = "--- src/test.java\n+++ src/test.java\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    service.patch_repo.get_by_id.return_value = patch_obj
    
    service.pr_repo.get_by_patch_id.return_value = None
    
    service.github_client.get_default_branch.return_value = "main"
    service.github_client.get_branch_sha.return_value = "abc123sha"
    service.github_client.get_file_sha.return_value = "file_sha"
    service.github_client.get_file_content.return_value = "old\n"
    service.github_client.create_pull_request.return_value = {"number": 1, "html_url": "http://pr"}
    
    # Since we don't have git installed or want to execute git apply in unit tests cleanly across all environments, 
    # we mock the subprocess.run call used in DeliveryService.
    with patch("subprocess.run") as mock_run, \
         patch("app.core.config.settings.github_token", "fake_token"):
         
        # Simulate subprocess modifying the file
        def fake_git_apply(*args, **kwargs):
            import os
            # write "new\n" to candidate.patch's target
            cwd = kwargs.get("cwd")
            with open(os.path.join(cwd, "src/test.java"), "w", encoding="utf-8") as f:
                f.write("new\n")
            return MagicMock(returncode=0)
            
        mock_run.side_effect = fake_git_apply
        
        response = service.run_delivery(incident.id, patch_obj.id, "https://github.com/sunilkumarb2007/JavaAPICheck")
        
        assert response.status == "pr_created"
        
        # Verify update_file was called with the base64 encoded "new\n"
        encoded_new = base64.b64encode(b"new\n").decode("utf-8")
        service.github_client.update_file.assert_called_once()
        args, kwargs = service.github_client.update_file.call_args
        assert args[4] == encoded_new # content_base64 argument
        assert "Applied patch:" not in base64.b64decode(args[4]).decode("utf-8") # Must not be just a comment wrapper

def test_delivery_handles_github_errors(mock_db):
    service = DeliveryService(mock_db)
    
    # Mocks
    service.incident_repo = MagicMock()
    service.patch_repo = MagicMock()
    service.pr_repo = MagicMock()
    service.github_client = MagicMock()
    
    incident = MagicMock()
    incident.id = uuid.uuid4()
    service.incident_repo.get_by_id.return_value = incident
    
    patch_obj = MagicMock()
    patch_obj.id = uuid.uuid4()
    patch_obj.incident_id = incident.id
    patch_obj.status = "validated"
    patch_obj.affected_files = ["src/test.java"]
    service.patch_repo.get_by_id.return_value = patch_obj
    
    service.pr_repo.get_by_patch_id.return_value = None
    
    # Simulate a 404 from get_file_content
    service.github_client.get_default_branch.return_value = "main"
    service.github_client.get_branch_sha.return_value = "abc123sha"
    service.github_client.get_file_sha.return_value = None
    service.github_client.get_file_content.side_effect = GitHubError("Not Found", 404)
    
    with patch("app.core.config.settings.github_token", "fake_token"):
        response = service.run_delivery(incident.id, patch_obj.id, "https://github.com/sunilkumarb2007/JavaAPICheck")
        
        assert response.status == "failed"
        assert "404" in response.error_details
        assert "Not Found" in response.error_details
