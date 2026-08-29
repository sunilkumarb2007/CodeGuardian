import os
import re
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigurationGuardianService:
    """
    Configuration Guardian & Drift Detection.
    Monitors configuration files, environment variable schemas, and application properties.
    Detects missing or drifted configuration and produces safe, evidence-based recovery proposals.
    STRICT RULE: Plaintext secret values are NEVER stored, logged, or sent to AI models.
    """

    @classmethod
    def audit_service_configuration(
        cls,
        repo_path: str,
        service_path: str,
        service_name: str,
        observed_env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Audits service configuration for missing variables, schema drift, and file references.
        """
        full_service_path = os.path.join(repo_path, service_path) if not os.path.isabs(service_path) else service_path
        
        # 1. Discover expected keys from code & manifests
        expected_keys = cls._discover_required_keys(full_service_path)
        
        # 2. Check observed environment keys (only key names, never storing secret values)
        observed_keys = set(observed_env.keys()) if observed_env else set()
        
        # Also check if local .env exists to extract key names only
        env_file_path = os.path.join(full_service_path, ".env")
        if os.path.exists(env_file_path):
            with open(env_file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        observed_keys.add(line.split("=", 1)[0].strip())

        # 3. Detect drift, missing keys, and compatibility
        drifts: List[Dict[str, Any]] = []
        
        for req in expected_keys:
            key = req["key"]
            if key not in observed_keys:
                is_secret = cls._is_secret_key(key)
                drifts.append({
                    "service": service_name,
                    "key_name": key,
                    "status": "MISSING",
                    "category": req["category"],
                    "source_file": req["source_file"],
                    "is_secret": is_secret,
                    "desired_state": "PRESENT",
                    "observed_state": "MISSING",
                    "recovery_proposal": cls._generate_safe_recovery_proposal(key, req["category"], is_secret)
                })

        return {
            "service_name": service_name,
            "total_expected": len(expected_keys),
            "total_observed": len(observed_keys),
            "drifts_detected": len(drifts),
            "status": "DRIFT_DETECTED" if drifts else "HEALTHY",
            "items": drifts,
            "audited_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def _discover_required_keys(cls, dir_path: str) -> List[Dict[str, Any]]:
        required_keys: List[Dict[str, Any]] = []
        seen = set()

        if not os.path.exists(dir_path):
            return required_keys

        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dir_path).replace("\\", "/")

                # Check template files
                if file in [".env.example", ".env.template", ".env.sample"]:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k = line.split("=", 1)[0].strip()
                                if k not in seen:
                                    seen.add(k)
                                    required_keys.append({
                                        "key": k,
                                        "category": "environment_template",
                                        "source_file": rel_path
                                    })

                # Check application.yml / properties
                elif file.endswith((".properties", ".yml", ".yaml")):
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for match in re.findall(r'\$\{([A-Z0-9_]+)(?::[^}]+)?\}', content):
                            if match not in seen:
                                seen.add(match)
                                required_keys.append({
                                    "key": match,
                                    "category": "application_properties",
                                    "source_file": rel_path
                                })

                # Check code references (Java System.getenv, Python os.environ / os.getenv, Node process.env)
                elif file.endswith((".java", ".py", ".ts", ".js", ".go")):
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # System.getenv("KEY")
                        for match in re.findall(r'System\.getenv\(\s*["\']([A-Z0-9_]+)["\']\s*\)', content):
                            if match not in seen:
                                seen.add(match)
                                required_keys.append({"key": match, "category": "code_reference", "source_file": rel_path})
                        # os.environ["KEY"] or os.getenv("KEY")
                        for match in re.findall(r'os\.(?:environ(?:\[|\.get\()|getenv\()\s*["\']([A-Z0-9_]+)["\']', content):
                            if match not in seen:
                                seen.add(match)
                                required_keys.append({"key": match, "category": "code_reference", "source_file": rel_path})
                        # process.env.KEY
                        for match in re.findall(r'process\.env\.([A-Z0-9_]+)', content):
                            if match not in seen:
                                seen.add(match)
                                required_keys.append({"key": match, "category": "code_reference", "source_file": rel_path})

        return required_keys

    @classmethod
    def _is_secret_key(cls, key: str) -> bool:
        k_upper = key.upper()
        secret_indicators = ["SECRET", "PASSWORD", "PASS", "TOKEN", "KEY", "AUTH", "CREDENTIAL", "PRIVATE"]
        return any(ind in k_upper for ind in secret_indicators)

    @classmethod
    def _generate_safe_recovery_proposal(cls, key: str, category: str, is_secret: bool) -> str:
        if is_secret:
            return f"Define '{key}' in your environment or secret manager (never commit secret values to repository)."
        if "PORT" in key:
            return f"Set '{key}=8080' in application environment."
        if "TIMEOUT" in key:
            return f"Set '{key}=5000' (default 5000ms timeout)."
        if "ENV" in key or "ENVIRONMENT" in key:
            return f"Set '{key}=development'."
        return f"Add '{key}=<configured_value>' to .env or container environment variables."
