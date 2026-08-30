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
    ALLOWED_NPM = ["npm", "npx", "pnpm", "yarn", "corepack"]
    ALLOWED_PYTHON = ["python", "python3", "pip", "pip3", "pytest", "poetry", "uv"]
    ALLOWED_GO = ["go"]
    ALLOWED_RUST = ["cargo", "rustc"]
    ALLOWED_DOTNET = ["dotnet"]
    ALLOWED_SHELL = ["bash", "sh"]
    ALLOWED_GIT = ["git", "patch"]
    
    # Safe Git commands
    ALLOWED_GIT_ARGS = [
        "clone", "status", "checkout", "branch", "apply", "diff", "commit", "push", "init", "add", "show", "remote", "ls-files"
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
            
        # 1. Reject dangerous shell operators in structured arguments
        for token in command:
            for danger in cls.DANGEROUS_TOKENS:
                if danger in token:
                    raise ValueError(f"COMMAND_REJECTED: Dangerous token '{danger}' detected in command arguments.")
                    
        raw_exec = command[0]
        # Normalize executable name
        clean_exec = raw_exec.replace("./", "").replace(".\\", "")
        executable = os.path.basename(clean_exec).lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]

        is_git = (architecture_build_system == "git" or executable in cls.ALLOWED_GIT)

        # 2. Reject directory traversal or absolute paths in arguments (except git clone targets)
        for token in command[1:]:
            if ".." in token:
                raise ValueError(f"COMMAND_REJECTED: Directory traversals are not allowed: {token}")
            if not is_git and (token.startswith("/") or token.startswith("\\") or os.path.isabs(token) or (len(token) > 2 and token[1] == ":")):
                raise ValueError(f"COMMAND_REJECTED: Absolute path references are not allowed: {token}")
            
        # Allow shell wrappers (bash, sh) when running a trusted repo wrapper script
        if executable in cls.ALLOWED_SHELL:
            if len(command) > 1:
                target_script = os.path.basename(command[1]).lower()
                if any(target_script.startswith(w) for w in ["mvnw", "gradlew", "test", "build"]):
                    return command
            return command

        # Git is always allowed for repository management
        if executable in cls.ALLOWED_GIT:
            return command
            
        # Java Maven
        if architecture_build_system == "maven":
            if executable not in cls.ALLOWED_MAVEN and executable not in cls.ALLOWED_SHELL:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Maven architecture")
            return command
            
        # Java Gradle
        elif architecture_build_system == "gradle":
            if executable not in cls.ALLOWED_GRADLE and executable not in cls.ALLOWED_SHELL:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Gradle architecture")
            return command
            
        # Node / NPM
        elif architecture_build_system in ["npm", "node"]:
            if executable not in cls.ALLOWED_NPM:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for NPM architecture")
            return command
            
        # Python
        elif architecture_build_system in ["pip", "python", "pytest"]:
            if executable not in cls.ALLOWED_PYTHON:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Python architecture")
            return command
            
        # Go
        elif architecture_build_system == "go":
            if executable not in cls.ALLOWED_GO:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Go architecture")
            return command

        # Rust
        elif architecture_build_system == "rust":
            if executable not in cls.ALLOWED_RUST:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for Rust architecture")
            return command

        # .NET
        elif architecture_build_system in ["dotnet", "csharp"]:
            if executable not in cls.ALLOWED_DOTNET:
                raise ValueError(f"COMMAND_REJECTED: Command '{executable}' not allowed for .NET architecture")
            return command

        else:
            # Fallback checks across all permitted build systems
            all_allowed = (
                cls.ALLOWED_MAVEN + cls.ALLOWED_GRADLE + cls.ALLOWED_NPM + 
                cls.ALLOWED_PYTHON + cls.ALLOWED_GO + cls.ALLOWED_RUST + 
                cls.ALLOWED_DOTNET + cls.ALLOWED_GIT + cls.ALLOWED_SHELL
            )
            if executable in all_allowed:
                return command
                
            raise ValueError(f"COMMAND_REJECTED: Command '{executable}' violates execution policy. Detected architecture: {architecture_build_system}")
