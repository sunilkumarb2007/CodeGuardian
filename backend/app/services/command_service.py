import subprocess
import time

import platform
import logging
from typing import List, Dict, Any, Optional
import os
from app.services.command_policy import CommandPolicy

logger = logging.getLogger(__name__)

class CommandExecutionService:
    MAX_OUTPUT_LENGTH = 1000000  # 1MB limit

    def __init__(self):
        pass

    def kill_process_tree(self, pid: int):
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                import signal
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Failed to kill process tree {pid}: {e}")

    def execute_command(self, command: List[str], cwd: str, timeout_seconds: int = 180, architecture: str = "unknown") -> Dict[str, Any]:
        """
        Executes a command safely without shell=True.
        Enforces execution boundaries via CommandPolicy.
        """
        if not isinstance(command, list):
            raise ValueError("Command must be a list of strings")

        # Validate command against architecture policy
        CommandPolicy.validate_command(command, architecture)

        started_at = time.time()
        use_shell = (platform.system() == "Windows")
        
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=use_shell
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                exit_code = process.returncode
                timed_out = False
            except subprocess.TimeoutExpired:
                self.kill_process_tree(process.pid)
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    stdout, stderr = "", "Process killed but streams did not close"
                    if getattr(process, 'stdout', None):
                        process.stdout.close()
                    if getattr(process, 'stderr', None):
                        process.stderr.close()
                exit_code = -1
                timed_out = True
                
        except Exception as e:
            stdout = ""
            stderr = str(e)
            exit_code = -1
            timed_out = False
            
        if stdout and len(stdout) > self.MAX_OUTPUT_LENGTH:
            stdout = stdout[-self.MAX_OUTPUT_LENGTH:] + "\n...[TRUNCATED]"
        if stderr and len(stderr) > self.MAX_OUTPUT_LENGTH:
            stderr = stderr[-self.MAX_OUTPUT_LENGTH:] + "\n...[TRUNCATED]"

        finished_at = time.time()
        duration_ms = int((finished_at - started_at) * 1000)

        return {
            "command": " ".join(command),
            "working_directory": cwd,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": timed_out
        }
