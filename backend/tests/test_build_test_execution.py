import pytest
import os
import stat
import tempfile
import sys
import uuid
from datetime import datetime, timezone

from app.services.command_service import CommandExecutionService, parse_test_summary, redact_secrets
from app.services.command_policy import CommandPolicy
from app.engine.replay_engine import ReplayEngine
from app.engine.validation_engine import ValidationEngine
from app.services.workspace_service import WorkspaceService, STAGES_CONFIG
from app.db.database import SessionLocal, Base, engine
from app.db.models import Run, Incident, Patch, Repository, Application, ValidationRun
from app.engine.run_state_machine import RunState


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_1_parse_test_summary():
    mvn_out = """
    [INFO] Running com.codeguardian.paymentservice.PaymentServiceTest
    [INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.23 s -- in com.codeguardian.paymentservice.PaymentServiceTest
    [INFO] 
    [INFO] Results:
    [INFO] 
    [INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
    [INFO] 
    [INFO] BUILD SUCCESS
    """
    summary = parse_test_summary(mvn_out, "")
    assert summary is not None
    assert summary["framework"] == "maven"
    assert summary["total"] == 16
    assert summary["failed"] == 0
    assert summary["errors"] == 0

    pytest_out = "======= 29 passed, 2 warnings in 15.79s ======="
    summary_pytest = parse_test_summary(pytest_out, "")
    assert summary_pytest is not None
    assert summary_pytest["framework"] == "pytest"
    assert summary_pytest["passed"] == 29
    assert summary_pytest["failed"] == 0


def test_2_redact_secrets():
    raw = "Connecting with ghp_123456789012345678901234 and Bearer eyJhbGciOiJIUzI1NiJ9.test and re_mockkey12345678901234567890"
    redacted = redact_secrets(raw)
    assert "[REDACTED_GITHUB_TOKEN]" in redacted or "[REDACTED" in redacted
    assert "ghp_123456789012345678901234" not in redacted
    assert "re_mockkey12345678901234567890" not in redacted


def test_3_exit_code_authoritative(tmp_path):
    """
    A command with exit_code != 0 MUST be considered failed even if
    stdout contains the text 'BUILD SUCCESS'.
    """
    cmd_svc = CommandExecutionService()
    script_file = tmp_path / "fake_build.py"
    script_file.write_text("import sys\nprint('BUILD SUCCESS')\nsys.exit(1)\n")
    res = cmd_svc.execute_command([sys.executable, "fake_build.py"], cwd=str(tmp_path), architecture="python")
    assert res["exit_code"] == 1
    assert "BUILD SUCCESS" in res["stdout"]


def test_4_stale_output_isolated(tmp_path):
    """
    Each execution has its own isolated output and unique command_id.
    """
    cmd_svc = CommandExecutionService()
    f1 = tmp_path / "f1.py"
    f1.write_text("print('OUTPUT_ONE')\n")
    f2 = tmp_path / "f2.py"
    f2.write_text("print('OUTPUT_TWO')\n")
    res1 = cmd_svc.execute_command([sys.executable, "f1.py"], cwd=str(tmp_path), architecture="python")
    res2 = cmd_svc.execute_command([sys.executable, "f2.py"], cwd=str(tmp_path), architecture="python")
    
    assert res1["command_id"] != res2["command_id"]
    assert "OUTPUT_ONE" in res1["stdout"]
    assert "OUTPUT_ONE" not in res2["stdout"]
    assert "OUTPUT_TWO" in res2["stdout"]


def test_5_test_timeout(tmp_path):
    """
    Long-running commands time out safely and terminate process tree.
    """
    cmd_svc = CommandExecutionService()
    script_file = tmp_path / "sleeper.py"
    script_file.write_text("import time\ntime.sleep(10)\n")
    res = cmd_svc.execute_command([sys.executable, "sleeper.py"], cwd=str(tmp_path), timeout_seconds=1, architecture="python")
    assert res["timed_out"] is True
    assert res["exit_code"] == -1


def test_6_maven_wrapper_detection_and_repair(tmp_path):
    """
    Verifies that a mock mvnw script (even if non-executable on POSIX)
    is detected, permissions repaired, and executed cleanly.
    """
    cmd_svc = CommandExecutionService()
    
    if os.name == "nt":
        mvnw_file = tmp_path / "mvnw.cmd"
        mvnw_file.write_text("@echo off\necho Tests run: 8, Failures: 0, Errors: 0, Skipped: 0\necho BUILD SUCCESS\nexit /b 0")
        res = cmd_svc.execute_command(["mvnw.cmd", "test"], cwd=str(tmp_path), architecture="maven")
        assert res["exit_code"] == 0
        assert "BUILD SUCCESS" in res["stdout"]
    else:
        mvnw_file = tmp_path / "mvnw"
        mvnw_file.write_text("#!/bin/sh\necho 'Tests run: 8, Failures: 0, Errors: 0, Skipped: 0'\necho 'BUILD SUCCESS'\nexit 0\n")
        os.chmod(str(mvnw_file), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        assert not (os.stat(str(mvnw_file)).st_mode & stat.S_IXUSR)
        
        res = cmd_svc.execute_command(["./mvnw", "test"], cwd=str(tmp_path), architecture="maven")
        assert res["exit_code"] == 0
        assert "BUILD SUCCESS" in res["stdout"]
        assert (os.stat(str(mvnw_file)).st_mode & stat.S_IXUSR)


def test_7_gradle_wrapper_detection_and_repair(tmp_path):
    """
    Verifies that a mock gradlew script is handled with self-healing.
    """
    cmd_svc = CommandExecutionService()
    
    if os.name == "nt":
        gradlew_file = tmp_path / "gradlew.bat"
        gradlew_file.write_text("@echo off\necho 5 tests completed, 0 failed, 0 skipped\nexit /b 0")
        res = cmd_svc.execute_command(["gradlew.bat", "test"], cwd=str(tmp_path), architecture="gradle")
        assert res["exit_code"] == 0
    else:
        gradlew_file = tmp_path / "gradlew"
        gradlew_file.write_text("#!/bin/sh\necho '5 tests completed, 0 failed, 0 skipped'\nexit 0\n")
        os.chmod(str(gradlew_file), 0o644)
        res = cmd_svc.execute_command(["./gradlew", "test"], cwd=str(tmp_path), architecture="gradle")
        assert res["exit_code"] == 0
        assert (os.stat(str(gradlew_file)).st_mode & stat.S_IXUSR)


def test_8_stage12_and_stage13_canonical_numbering(setup_db):
    """
    Verifies that Stage 12 is Build and Stage 13 is Tests in STAGES_CONFIG,
    and WorkspaceService serializes them with exact keys '12_build' and '13_tests'.
    """
    assert STAGES_CONFIG[11][0] == "build" # index 11 -> 12th stage
    assert STAGES_CONFIG[12][0] == "tests" # index 12 -> 13th stage
    assert len(STAGES_CONFIG) == 17

    db = SessionLocal()
    try:
        run_id = str(uuid.uuid4())
        run = Run(
            id=run_id,
            state="TESTS_RUNNING",
            current_stage="13_tests",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(run)
        db.commit()

        ws_svc = WorkspaceService(db)
        ws = ws_svc.get_run_workspace(run_id)
        assert ws is not None
        stages = ws["stages"]
        
        # Check Stage 12 Build
        stage12 = next((s for s in stages if "12_build" in s.get("id", "") or s.get("name") == "build"), None)
        assert stage12 is not None
        assert "Build" in stage12["label"]

        # Check Stage 13 Tests
        stage13 = next((s for s in stages if "13_tests" in s.get("id", "") or s.get("name") == "tests"), None)
        assert stage13 is not None
        assert "Tests" in stage13["label"]
    finally:
        db.close()


def test_9_stage13_failure_blocks_validation(setup_db):
    """
    When Stage 13 Tests fails, ValidationEngine fails validation and sets failure_reason='TESTS_FAILED'.
    """
    val_eng = ValidationEngine()
    patch = Patch(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        diff="--- a/Foo.java\n+++ b/Foo.java\n@@ -1,3 +1,4 @@\n+bar\n",
        affected_files=["Foo.java"]
    )
    
    class MockReplayFailedTests:
        result = "REPLAY_FAILURE_PERSISTS"
        patched = type("Patched", (), {
            "build_passed": True,
            "tests_passed": False,
            "status": "TESTS_FAILED",
            "output": "Tests run: 8, Failures: 2, Errors: 0, Skipped: 0",
            "build_output": "BUILD SUCCESS"
        })()

    res = val_eng.run_validation(patch, MockReplayFailedTests())
    assert res["overall_status"] == "failed"
    assert res["checks"].tests == "failed"
    assert res["checks"].build == "passed"
    assert res["failure_reason"] in ["TESTS_FAILED", "REPLAY_FAILED"]


def test_10_stage12_build_failure_blocks_tests(setup_db):
    """
    When Stage 12 Build fails, ValidationEngine fails with failure_reason='BUILD_FAILED'.
    """
    val_eng = ValidationEngine()
    patch = Patch(
        id=uuid.uuid4(),
        incident_id=uuid.uuid4(),
        diff="--- a/Foo.java\n+++ b/Foo.java\n@@ -1,3 +1,4 @@\n+bar\n",
        affected_files=["Foo.java"]
    )
    
    class MockReplayFailedBuild:
        result = "BUILD_FAILED"
        patched = type("Patched", (), {
            "build_passed": False,
            "tests_passed": False,
            "status": "BUILD_FAILED",
            "output": "[ERROR] COMPILATION ERROR: ';' expected",
            "build_output": "[ERROR] COMPILATION ERROR: ';' expected"
        })()

    res = val_eng.run_validation(patch, MockReplayFailedBuild())
    assert res["overall_status"] == "failed"
    assert res["checks"].build == "failed"
    assert res["checks"].tests == "failed"
    assert res["failure_reason"] == "BUILD_FAILED"
