import pytest
import os
from app.services.command_policy import CommandPolicy
from app.engine.replay_engine import ReplayEngine
from app.db.models import Patch

def test_command_policy_rejects_injection():
    # Test shell injection operators
    for token in ["&&", ";", "|", "||", ">", ">>", "<", "&", "`", "$(", "${"]:
        with pytest.raises(ValueError, match="COMMAND_REJECTED"):
            CommandPolicy.validate_command(["mvn", "test", token, "malicious"], "maven")

def test_command_policy_rejects_absolute_paths():
    # Test absolute paths
    with pytest.raises(ValueError, match="COMMAND_REJECTED"):
        CommandPolicy.validate_command(["python", "/etc/passwd"], "pip")
    with pytest.raises(ValueError, match="COMMAND_REJECTED"):
        CommandPolicy.validate_command(["python", "C:\\Windows\\System32\\cmd.exe"], "pip")
    with pytest.raises(ValueError, match="COMMAND_REJECTED"):
        CommandPolicy.validate_command(["python", "../../../secret.txt"], "pip")

def test_replay_engine_rejects_path_traversal():
    engine = ReplayEngine()
    
    # Test typical patch with traversal
    patch = Patch(
        id="123",
        incident_id="456",
        diff="""--- a/../../../etc/passwd
+++ b/../../../etc/passwd
@@ -1 +1 @@
-root:x:0:0:root:/root:/bin/bash
+hacked
""",
        affected_files=[],
        status="generated"
    )
    
    # Engine should reject
    assert engine._apply_patch(".", patch) == False

def test_replay_engine_rejects_absolute_path_patch():
    engine = ReplayEngine()
    
    # Test patch with absolute Windows path
    patch = Patch(
        id="123",
        incident_id="456",
        diff="""--- a/C:/Windows/System32/config/SAM
+++ b/C:/Windows/System32/config/SAM
@@ -1 +1 @@
-foo
+bar
""",
        affected_files=[],
        status="generated"
    )
    
    # Engine should reject
    assert engine._apply_patch(".", patch) == False

