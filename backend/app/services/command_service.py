import subprocess
import time
import platform
import logging
import os
import stat
import uuid
import re
import shutil
from typing import List, Dict, Any, Optional
from app.services.command_policy import CommandPolicy

logger = logging.getLogger(__name__)


def redact_secrets(text: str) -> str:
    """Redacts tokens, passwords, and private keys from output strings."""
    if not text:
        return ""
    # Redact GitHub tokens
    text = re.sub(r'ghp_[A-Za-z0-9_]{20,}', '[REDACTED_GITHUB_TOKEN]', text)
    text = re.sub(r'github_pat_[A-Za-z0-9_]{20,}', '[REDACTED_GITHUB_PAT]', text)
    # Redact Resend keys
    text = re.sub(r're_[A-Za-z0-9_]{20,}', '[REDACTED_RESEND_KEY]', text)
    # Redact Sarvam / API keys
    text = re.sub(r'sk_[A-Za-z0-9_]{20,}', '[REDACTED_API_KEY]', text)
    # Redact Authorization Bearer headers
    text = re.sub(r'Bearer\s+[A-Za-z0-9\-_.]+', 'Bearer [REDACTED_TOKEN]', text)
    return text


def parse_test_summary(stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
    """
    Parses test counts from build tool output (Maven, Gradle, Pytest, Go, Rust, NPM).
    """
    combined = f"{stdout}\n{stderr}"
    
    # 1. Maven Surefire / Failsafe
    # Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
    # or Tests run: 8,  Failures: 0,  Errors: 0,  Skipped: 0
    m_mvn = re.findall(r'Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)', combined, re.IGNORECASE)
    if m_mvn:
        # Sum all surefire test runs if multiple modules reported
        total_run = sum(int(x[0]) for x in m_mvn)
        total_failures = sum(int(x[1]) for x in m_mvn)
        total_errors = sum(int(x[2]) for x in m_mvn)
        total_skipped = sum(int(x[3]) for x in m_mvn)
        total_passed = max(0, total_run - total_failures - total_errors - total_skipped)
        return {
            "framework": "maven",
            "total": total_run,
            "passed": total_passed,
            "failed": total_failures,
            "errors": total_errors,
            "skipped": total_skipped
        }
        
    # 2. Pytest
    # 15 passed, 2 failed, 1 error, 3 skipped in 4.5s
    m_pytest_pass = re.search(r'(\d+)\s+passed', combined)
    m_pytest_fail = re.search(r'(\d+)\s+failed', combined)
    m_pytest_err = re.search(r'(\d+)\s+error', combined)
    m_pytest_skip = re.search(r'(\d+)\s+skipped', combined)
    if m_pytest_pass or m_pytest_fail or m_pytest_err:
        passed = int(m_pytest_pass.group(1)) if m_pytest_pass else 0
        failed = int(m_pytest_fail.group(1)) if m_pytest_fail else 0
        errors = int(m_pytest_err.group(1)) if m_pytest_err else 0
        skipped = int(m_pytest_skip.group(1)) if m_pytest_skip else 0
        return {
            "framework": "pytest",
            "total": passed + failed + errors + skipped,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped
        }

    # 3. Gradle
    # 8 tests completed, 0 failed, 0 skipped
    m_gradle = re.search(r'(\d+)\s+tests?\s+completed,\s*(\d+)\s+failed,\s*(\d+)\s+skipped', combined, re.IGNORECASE)
    if m_gradle:
        total = int(m_gradle.group(1))
        failed = int(m_gradle.group(2))
        skipped = int(m_gradle.group(3))
        return {
            "framework": "gradle",
            "total": total,
            "passed": max(0, total - failed - skipped),
            "failed": failed,
            "errors": 0,
            "skipped": skipped
        }

    # 4. Cargo / Rust
    # test result: ok. 12 passed; 0 failed; 0 ignored
    m_cargo = re.search(r'test result:\s*(?:ok|FAILED)\.\s*(\d+)\s+passed;\s*(\d+)\s+failed;\s*(\d+)\s+ignored', combined)
    if m_cargo:
        passed = int(m_cargo.group(1))
        failed = int(m_cargo.group(2))
        skipped = int(m_cargo.group(3))
        return {
            "framework": "cargo",
            "total": passed + failed + skipped,
            "passed": passed,
            "failed": failed,
            "errors": 0,
            "skipped": skipped
        }

    return None


class CommandExecutionService:
    MAX_OUTPUT_LENGTH = 1000000  # 1MB limit

    def __init__(self):
        pass

    def kill_process_tree(self, pid: int):
        """Safely terminates a process and all its child processes."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                import signal
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except Exception:
                    os.kill(pid, signal.SIGTERM)
        except Exception as e:
            logger.debug(f"Process tree termination note for pid {pid}: {e}")

    def execute_command(
        self,
        command: List[str],
        cwd: str,
        timeout_seconds: int = 180,
        architecture: str = "unknown",
        auto_recover_wrapper: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a command safely with structured arguments, isolated buffers,
        exit code authority, wrapper permission self-healing, and attempt tracking.
        """
        if not isinstance(command, list):
            raise ValueError("Command must be a list of strings")

        # Validate command against architecture policy
        CommandPolicy.validate_command(command, architecture)

        is_windows = (platform.system() == "Windows")
        attempts_history = []
        final_recovery_action = None
        command_id = str(uuid.uuid4())

        # Determine candidate commands to try in order of preference
        commands_to_try: List[tuple[List[str], str]] = []
        raw_cmd = list(command)
        exec_name = raw_cmd[0]
        base_name = os.path.basename(exec_name.replace("./", "").replace(".\\", "")).lower()

        # Check if wrapper script
        is_maven_wrapper = base_name in ["mvnw", "mvnw.cmd"]
        is_gradle_wrapper = base_name in ["gradlew", "gradlew.bat"]

        if is_windows:
            if is_maven_wrapper:
                # Windows prefers mvnw.cmd
                target_wrapper = "mvnw.cmd" if os.path.exists(os.path.join(cwd, "mvnw.cmd")) else ("mvnw.bat" if os.path.exists(os.path.join(cwd, "mvnw.bat")) else "mvn.cmd")
                commands_to_try.append(([target_wrapper] + raw_cmd[1:], "WINDOWS_CMD_WRAPPER"))
                if shutil.which("mvn"):
                    commands_to_try.append((["mvn"] + raw_cmd[1:], "SYSTEM_MVN_FALLBACK"))
            elif is_gradle_wrapper:
                target_wrapper = "gradlew.bat" if os.path.exists(os.path.join(cwd, "gradlew.bat")) else "gradle.bat"
                commands_to_try.append(([target_wrapper] + raw_cmd[1:], "WINDOWS_GRADLEW_BAT"))
                if shutil.which("gradle"):
                    commands_to_try.append((["gradle"] + raw_cmd[1:], "SYSTEM_GRADLE_FALLBACK"))
            else:
                commands_to_try.append((raw_cmd, "STANDARD_EXECUTION"))
        else:
            # POSIX (Linux / Render / macOS)
            if is_maven_wrapper:
                wrapper_file = os.path.join(cwd, "mvnw")
                if os.path.exists(wrapper_file):
                    # 1. Native wrapper execution with automatic chmod +x
                    commands_to_try.append((["./mvnw"] + raw_cmd[1:], "POSIX_WRAPPER_CHMOD_REPAIR"))
                    # 2. Trusted shell wrapper fallback
                    commands_to_try.append((["bash", "mvnw"] + raw_cmd[1:], "BASH_WRAPPER_FALLBACK"))
                    commands_to_try.append((["sh", "mvnw"] + raw_cmd[1:], "SH_WRAPPER_FALLBACK"))
                if shutil.which("mvn"):
                    commands_to_try.append((["mvn"] + raw_cmd[1:], "SYSTEM_MVN_FALLBACK"))
            elif is_gradle_wrapper:
                wrapper_file = os.path.join(cwd, "gradlew")
                if os.path.exists(wrapper_file):
                    commands_to_try.append((["./gradlew"] + raw_cmd[1:], "POSIX_WRAPPER_CHMOD_REPAIR"))
                    commands_to_try.append((["bash", "gradlew"] + raw_cmd[1:], "BASH_WRAPPER_FALLBACK"))
                    commands_to_try.append((["sh", "gradlew"] + raw_cmd[1:], "SH_WRAPPER_FALLBACK"))
                if shutil.which("gradle"):
                    commands_to_try.append((["gradle"] + raw_cmd[1:], "SYSTEM_GRADLE_FALLBACK"))
            else:
                commands_to_try.append((raw_cmd, "STANDARD_EXECUTION"))

        if not commands_to_try:
            commands_to_try.append((raw_cmd, "STANDARD_EXECUTION"))

        # Execute with wrapper recovery
        last_result = None
        started_overall = time.time()

        for attempt_idx, (cmd_argv, recovery_label) in enumerate(commands_to_try, start=1):
            # If POSIX and wrapper file exists, proactively ensure +x permission in isolated sandbox
            if not is_windows and auto_recover_wrapper:
                target_exec = cmd_argv[0].replace("./", "")
                full_exec_path = os.path.join(cwd, target_exec)
                if os.path.isfile(full_exec_path):
                    try:
                        current_mode = os.stat(full_exec_path).st_mode
                        if not (current_mode & stat.S_IXUSR):
                            os.chmod(full_exec_path, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                            logger.info(f"Proactively set executable bit (+x) on {target_exec} in sandbox workspace.")
                    except Exception as perm_err:
                        logger.debug(f"Isolated chmod note on {full_exec_path}: {perm_err}")

            started_at = time.time()
            use_shell = is_windows
            process_created = False
            stdout = ""
            stderr = ""
            exit_code = -1
            timed_out = False
            launch_error = None

            try:
                process = subprocess.Popen(
                    cmd_argv,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=use_shell
                )
                process_created = True
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout_seconds)
                    exit_code = process.returncode
                    timed_out = False
                except subprocess.TimeoutExpired:
                    self.kill_process_tree(process.pid)
                    try:
                        stdout, stderr = process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        stdout, stderr = "", "Process killed on timeout; streams did not close"
                    exit_code = -1
                    timed_out = True
                    
            except PermissionError as pe:
                launch_error = f"[Errno 13] Permission denied: {cmd_argv[0]}"
                stderr = launch_error
                exit_code = -1
            except FileNotFoundError as fe:
                launch_error = f"Executable not found: {cmd_argv[0]}"
                stderr = launch_error
                exit_code = -1
            except Exception as e:
                launch_error = str(e)
                stderr = launch_error
                exit_code = -1

            finished_at = time.time()
            duration_ms = int((finished_at - started_at) * 1000)

            # Redact secrets
            clean_stdout = redact_secrets(stdout or "")
            clean_stderr = redact_secrets(stderr or "")

            if clean_stdout and len(clean_stdout) > self.MAX_OUTPUT_LENGTH:
                clean_stdout = clean_stdout[-self.MAX_OUTPUT_LENGTH:] + "\n...[TRUNCATED]"
            if clean_stderr and len(clean_stderr) > self.MAX_OUTPUT_LENGTH:
                clean_stderr = clean_stderr[-self.MAX_OUTPUT_LENGTH:] + "\n...[TRUNCATED]"

            attempt_record = {
                "attempt": attempt_idx,
                "command": " ".join(cmd_argv),
                "strategy": recovery_label,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "timed_out": timed_out,
                "launch_error": launch_error
            }
            attempts_history.append(attempt_record)

            last_result = {
                "command_id": command_id,
                "command": " ".join(cmd_argv),
                "working_directory": cwd,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "stdout": clean_stdout,
                "stderr": clean_stderr,
                "timed_out": timed_out,
                "attempts": attempts_history,
                "recovery_action": recovery_label if attempt_idx > 1 else None,
                "test_summary": parse_test_summary(clean_stdout, clean_stderr)
            }

            # If the command executed with exit_code == 0 or was a genuine test run that returned non-zero test failure (not a launch error),
            # we do not need to try shell fallbacks.
            if exit_code == 0:
                final_recovery_action = recovery_label if attempt_idx > 1 else None
                break
            
            # If it's not a launch error (e.g. process ran and tests legitimately failed with exit_code != 0), stop retrying
            if process_created and not launch_error:
                # Process actually executed the test suite, so test failure is genuine
                break

        return last_result or {
            "command_id": command_id,
            "command": " ".join(command),
            "working_directory": cwd,
            "started_at": started_overall,
            "finished_at": time.time(),
            "duration_ms": int((time.time() - started_overall) * 1000),
            "exit_code": -1,
            "stdout": "",
            "stderr": "No command execution attempted",
            "timed_out": False,
            "attempts": attempts_history,
            "recovery_action": None,
            "test_summary": None
        }
