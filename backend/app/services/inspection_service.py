import os
import shutil
import tempfile
import logging
from urllib.parse import urlparse
from app.schemas.orchestration import InspectionResult, ArchitectureSummary
from app.services.command_service import CommandExecutionService
from app.services.git_workspace import GitWorkspace

logger = logging.getLogger(__name__)

class RepositoryInspectionService:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")

    def inspect_repository(self, repository_url: str, db=None, repository_id=None) -> InspectionResult:
        logger.info(f"Starting inspection for {repository_url}")
        logger.error(f"DEBUG: db is {db is not None}, repository_id is {repository_id}")
        
        # 1. Clone repository to temp directory
        if repository_id:
            workspace_root = os.path.join(tempfile.gettempdir(), "codeguardian_workspaces")
            temp_dir = os.path.join(workspace_root, "repositories", str(repository_id), "source")
            os.makedirs(temp_dir, exist_ok=True)
        else:
            temp_dir = tempfile.mkdtemp(prefix="codeguardian_")
            
        try:
            # If the directory is already populated, don't download again (Phase D reuse)
            if not os.listdir(temp_dir):
                self._clone_repo(repository_url, temp_dir)
            
            # 2. Analyze Architecture
            architecture = self._analyze_architecture(temp_dir)
            
            # 2.5 Ingest source files if DB provided
            if db and repository_id:
                from app.db.models import RepositoryFile
                import uuid
                from typing import Optional
                from datetime import datetime, timezone
                # Clean old files to avoid duplicate clutter
                db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository_id).delete()
                
                # Ignored directories
                ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.idea', '.vscode'}
                
                # Walk temp_dir and ingest
                files_ingested = 0
                logger.error(f"DEBUG: Walking {temp_dir}")
                for root, dirs, files in os.walk(temp_dir):
                    dirs[:] = [d for d in dirs if d not in ignored_dirs]
                    
                    for file in files:
                        if file.endswith(('.py', '.java', '.js', '.ts', '.go', '.rs', '.json', '.xml', '.yml', '.yaml', '.txt', '.md', '.gradle', '.kts')):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, temp_dir).replace('\\', '/')
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                db.add(RepositoryFile(
                                    id=uuid.uuid4(),
                                    repository_id=repository_id,
                                    file_path=rel_path,
                                    source_snapshot=content,
                                    created_at=datetime.now(timezone.utc),
                                    updated_at=datetime.now(timezone.utc)
                                ))
                                files_ingested += 1
                            except Exception as e:
                                logger.warning(f"Failed to ingest file {rel_path}: {e}")
                logger.error(f"DEBUG: Ingested {files_ingested} files")
                db.commit()
                check_files = db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository_id).all()
                logger.error(f"DEBUG: Check files directly after flush: {len(check_files)}")
            
            # 3. Detect build/test failures
            build_passed, test_passed, failure_output, details = self._run_static_checks(temp_dir, architecture)
            
            return InspectionResult(
                repository_url=repository_url,
                architecture=architecture,
                static_analysis_passed=build_passed and test_passed,
                build_passed=build_passed,
                test_passed=test_passed,
                failure_output=failure_output,
                static_analysis_details=details
            )
            
        finally:
            if not repository_id:
                from app.core.workspace import remove_repository_workspace
                remove_repository_workspace(temp_dir)

    def _clone_repo(self, url: str, target_dir: str):
        logger.info(f"Cloning {url} into {target_dir}")
        git = GitWorkspace(os.path.dirname(target_dir))
        res = git.clone(url, target_dir)
        if res.get("exit_code") != 0:
            error_msg = res.get("stderr", "Unknown Git Error")
            logger.error(f"Clone failed: {error_msg}")
            raise RuntimeError(f"Failed to clone repository: {error_msg}")

    def _analyze_architecture(self, repo_dir: str) -> ArchitectureSummary:
        tech_stack = []
        language = None
        framework = None
        build_system = None
        test_framework = None
        source_root = None
        test_root = None
        build_cmd = None
        test_cmd = None
        config_files = []
        has_docker = os.path.exists(os.path.join(repo_dir, "Dockerfile"))
        
        if os.path.exists(os.path.join(repo_dir, "package.json")):
            tech_stack.extend(["Node.js", "JavaScript/TypeScript"])
            language = "javascript/typescript"
            framework = "node"
            build_system = "npm"
            test_framework = "jest/vitest"
            build_cmd = "npm run build"
            test_cmd = "npm test"
            source_root = "src"
            test_root = "test"
            config_files.append("package.json")
            
            try:
                with open(os.path.join(repo_dir, "package.json"), "r") as f:
                    content = f.read()
                    if "react" in content:
                        tech_stack.append("React")
                        framework = "react"
            except Exception:
                pass
            
        elif any(os.path.exists(os.path.join(repo_dir, f)) for f in ["requirements.txt", "pyproject.toml", "setup.py"]):
            tech_stack.append("Python")
            language = "python"
            build_system = "pip"
            test_framework = "pytest"
            build_cmd = "pip install -r requirements.txt"
            test_cmd = "pytest"
            source_root = "."
            test_root = "tests"
            for f in ["requirements.txt", "pyproject.toml", "setup.py"]:
                if os.path.exists(os.path.join(repo_dir, f)):
                    config_files.append(f)
            
        elif os.path.exists(os.path.join(repo_dir, "pom.xml")):
            tech_stack.append("Java")
            language = "java"
            build_system = "maven"
            test_framework = "junit"
            build_cmd = "mvn package -DskipTests"
            test_cmd = "mvn test"
            source_root = "src/main/java"
            test_root = "src/test/java"
            config_files.append("pom.xml")
            
        elif os.path.exists(os.path.join(repo_dir, "build.gradle")) or os.path.exists(os.path.join(repo_dir, "build.gradle.kts")):
            tech_stack.append("Java/Kotlin")
            language = "Java"
            build_system = "gradle"
            test_framework = "junit"
            build_cmd = "gradle build -x test"
            test_cmd = "gradle test"
            source_root = "src/main"
            test_root = "src/test"
            config_files.append("build.gradle") if os.path.exists(os.path.join(repo_dir, "build.gradle")) else config_files.append("build.gradle.kts")
            
        return ArchitectureSummary(
            tech_stack=tech_stack,
            language=language,
            framework=framework,
            build_system=build_system,
            test_framework=test_framework,
            has_docker=has_docker,
            source_root=source_root,
            test_root=test_root,
            build_command=build_cmd,
            test_command=test_cmd,
            configuration_files=config_files
        )

    def _run_static_checks(self, repo_dir: str, arch: ArchitectureSummary):
        import time
        from datetime import datetime, timezone
        
        build_passed = True
        test_passed = True
        failure_output = None
        details = {
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "command": "",
            "duration": 0.0,
            "working_directory": repo_dir,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        cmd = []
        if arch.test_framework == "pytest":
            cmd = ["pytest"]
        elif arch.test_framework == "jest/vitest":
            cmd = ["npm", "test"]
        elif arch.build_system == "maven":
            mvn = "C:\\Users\\sunil\\maven\\apache-maven-3.8.8\\bin\\mvn.cmd"
            cmd = [mvn, "clean", "test"]
        elif arch.build_system == "gradle":
            gradlew_cmd = "gradlew.bat" if os.name == 'nt' else "./gradlew"
            gradle = gradlew_cmd if os.path.exists(os.path.join(repo_dir, "gradlew")) or os.path.exists(os.path.join(repo_dir, "gradlew.bat")) else "gradle"
            cmd = [gradle, "test"]
            
        if not cmd:
            return build_passed, test_passed, failure_output, details
            
        details["command"] = " ".join(cmd)
        
        start_time = time.time()
        try:
            cmd_svc = CommandExecutionService()
            # Pre-requisites
            if arch.test_framework == "pytest":
                cmd_svc.execute_command(["pip", "install", "-r", "requirements.txt"], cwd=repo_dir, timeout=180)
            elif arch.test_framework == "jest/vitest":
                cmd_svc.execute_command(["npm", "install"], cwd=repo_dir, timeout=180)
            
            # Execute main test command
            res = cmd_svc.execute_command(cmd, cwd=repo_dir, timeout=300, architecture=arch.build_system)
            details["exit_code"] = res.get("exit_code", -1)
            details["stdout"] = res.get("stdout", "")
            details["stderr"] = res.get("stderr", "")
            if res.get("exit_code") != 0:
                test_passed = False
                failure_output = details["stdout"] + "\n" + details["stderr"]
        except Exception as e:
            test_passed = False
            failure_output = str(e)
            details["stderr"] = str(e)
            details["exit_code"] = -1
            
        details["duration"] = time.time() - start_time
        return build_passed, test_passed, failure_output, details
