import logging
import os
from typing import List

logger = logging.getLogger(__name__)

class CommandPolicy:
    """
    Enforces safe command execution based on detected architecture.
    Prevents arbitrary AI shell injection by allowing only known executables and fixed arguments.
    """

    ALLOWED_MAVEN = ["mvn", "mvnw", "mvnw.cmd", "mvn.cmd"]
    ALLOWED_GRADLE = ["gradle", "gradlew", "gradlew.bat", "gradle.bat"]
    ALLOWED_NPM = ["npm", "npx"]
    ALLOWED_PYTHON = ["python", "pip", "pytest"]
    ALLOWED_GIT = ["git", "patch"]
    
    # Safe Git commands
    ALLOWED_GIT_ARGS = [
        "clone", "status", "checkout", "branch", "apply", "diff", "commit", "push", "init", "add", "show", "remote"
    ]

    # Shell operators that denote injection
    DANGEROUS_TOKENS = ["&&", ";", "|", "||", ">", ">>", "<", "&", "`", "$(", "${"]

    @classmethod
    def validate_command(cls, command: List[str], architecture_build_system: str = "unknown") -> List[str]:
        """
        Validates the command array and returns the validated array if allowed.
        Raises ValueError if the command violates the policy.
        """
        if not command:
            raise ValueError("Command cannot be empty")
            
        # 1. Reject shell operators (even though shell=False prevents most, this adds defense-in-depth)
        for token in command:
            for danger in cls.DANGEROUS_TOKENS:
                if danger in token:
                    raise ValueError(f"COMMAND_REJECTED: Dangerous token '{danger}' detected in command arguments.")
                    
        # 2. Reject directory traversal and absolute paths in arguments
        for token in command[1:]:
            if ".." in token:
                raise ValueError(f"COMMAND_REJECTED: Directory traversals are not allowed: {token}")
            if os.path.isabs(token) or token.startswith("/") or token.startswith("\\") or (len(token) > 1 and token[1] == ":"):
                token_lower = token.lower()
                if not token_lower.startswith("/tmp/codeguardian_workspaces") and not token_lower.startswith("c:\\users\\") and not token_lower.startswith("d:\\"):
                    raise ValueError(f"COMMAND_REJECTED: Absolute paths are not allowed outside workspace: {token}")

        executable = os.path.basename(command[0]).lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]
            
        # Git is always allowed for repository management (GitWorkspace)
        if executable in cls.ALLOWED_GIT:
            if len(command) > 1 and command[1] not in cls.ALLOWED_GIT_ARGS:
                pass 
            return command
            
        # Java Maven
        if architecture_build_system == "maven":
            if executable not in cls.ALLOWED_MAVEN:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Maven architecture")
            return command
            
        # Java Gradle
        elif architecture_build_system == "gradle":
            if executable not in cls.ALLOWED_GRADLE:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Gradle architecture")
            return command
            
        # Node / NPM
        elif architecture_build_system == "npm":
            if executable not in cls.ALLOWED_NPM:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for NPM architecture")
            return command
            
        # Python
        elif architecture_build_system == "pip":
            if executable not in cls.ALLOWED_PYTHON:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Python architecture")
            return command
            
        else:
            # Fallback checks
            if executable in cls.ALLOWED_MAVEN + cls.ALLOWED_GRADLE + cls.ALLOWED_NPM + cls.ALLOWED_PYTHON + cls.ALLOWED_GIT:
                return command
                
            raise ValueError(f"COMMAND_REJECTED: Command '{executable}' violates execution policy. Detected architecture: {architecture_build_system}")
