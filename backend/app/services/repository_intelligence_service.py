import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global in-memory cache keyed by (repo_path or commit_sha)
_INTELLIGENCE_CACHE: Dict[str, Dict[str, Any]] = {}

class RepositoryIntelligenceService:
    """
    Comprehensive repository-wide intelligence layer.
    Extracts multi-service architecture, service inventory, cross-service dependency graphs,
    symbol indices, endpoint indices, and configuration manifests from real repository structure.
    """

    @classmethod
    def analyze_repository(cls, repo_path: str, commit_sha: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"{repo_path}:{commit_sha or 'latest'}"
        if cache_key in _INTELLIGENCE_CACHE:
            logger.info(f"Reusing cached repository intelligence for {cache_key}")
            return _INTELLIGENCE_CACHE[cache_key]

        if not os.path.exists(repo_path):
            logger.warning(f"Repository path does not exist: {repo_path}")
            return cls._empty_intelligence()

        # 1. Discover microservices & build manifests
        services = cls._discover_services(repo_path)
        arch_type = cls._classify_architecture(repo_path, services)

        # 2. Build cross-service dependency graph
        service_graph = cls._build_service_graph(repo_path, services)

        # 3. Build symbol & endpoint index
        symbols, endpoints = cls._index_symbols_and_endpoints(repo_path, services)

        # 4. Extract configuration manifests & required keys
        config_manifest = cls._extract_configuration_manifest(repo_path, services)

        intelligence = {
            "architecture_type": arch_type,
            "services_inventory": services,
            "service_graph": service_graph,
            "dependency_graph": service_graph.get("dependencies", {}),
            "symbol_index": symbols,
            "endpoint_index": endpoints,
            "config_manifest": config_manifest,
            "commit_sha": commit_sha or "HEAD",
            "analyzed_at": datetime.utcnow().isoformat()
        }

        _INTELLIGENCE_CACHE[cache_key] = intelligence
        return intelligence

    @classmethod
    def _discover_services(cls, root_path: str) -> List[Dict[str, Any]]:
        services: List[Dict[str, Any]] = []
        
        # Check subdirectories for distinct services
        subdirs = [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d)) and not d.startswith('.')]
        
        for subdir in subdirs:
            service_path = os.path.join(root_path, subdir)
            manifest = cls._inspect_service_directory(service_path, subdir)
            if manifest:
                manifest["relative_path"] = subdir
                services.append(manifest)

        # If no subservices found, treat root as single application
        if not services:
            root_manifest = cls._inspect_service_directory(root_path, os.path.basename(root_path) or "root-application")
            if root_manifest:
                root_manifest["relative_path"] = "."
                services.append(root_manifest)

        return services

    @classmethod
    def _inspect_service_directory(cls, dir_path: str, name: str) -> Optional[Dict[str, Any]]:
        files = os.listdir(dir_path) if os.path.exists(dir_path) else []
        
        language = "Unknown"
        framework = "Standard"
        build_tool = "Unknown"
        dependencies: List[str] = []
        databases: List[str] = []
        queues: List[str] = []
        ports: List[int] = []

        # Java / Maven / Gradle
        if "pom.xml" in files:
            language = "Java"
            build_tool = "Maven"
            pom_content = cls._read_file_safe(os.path.join(dir_path, "pom.xml"))
            if "spring-boot" in pom_content:
                framework = "Spring Boot"
            if "postgresql" in pom_content or "postgres" in pom_content:
                databases.append("PostgreSQL")
            if "mysql" in pom_content:
                databases.append("MySQL")
            if "kafka" in pom_content:
                queues.append("Kafka")
            if "rabbitmq" in pom_content or "amqp" in pom_content:
                queues.append("RabbitMQ")
        elif "build.gradle" in files or "build.gradle.kts" in files:
            language = "Java/Kotlin"
            build_tool = "Gradle"
            gradle_content = cls._read_file_safe(os.path.join(dir_path, "build.gradle")) or cls._read_file_safe(os.path.join(dir_path, "build.gradle.kts"))
            if "spring" in gradle_content:
                framework = "Spring Boot"

        # Node / TypeScript / JavaScript
        elif "package.json" in files:
            pkg_content = cls._read_file_safe(os.path.join(dir_path, "package.json"))
            try:
                pkg_data = json.loads(pkg_content)
                language = "TypeScript" if any(f.endswith(".ts") or f.endswith(".tsx") for _, _, fs in os.walk(dir_path) for f in fs) else "JavaScript"
                build_tool = "npm/yarn"
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                if "next" in deps:
                    framework = "Next.js"
                elif "react" in deps:
                    framework = "React"
                elif "express" in deps:
                    framework = "Express"
                elif "fastify" in deps:
                    framework = "Fastify"
                
                if "pg" in deps or "typeorm" in deps or "prisma" in deps:
                    databases.append("PostgreSQL")
                if "redis" in deps or "ioredis" in deps:
                    databases.append("Redis")
                if "amqplib" in deps:
                    queues.append("RabbitMQ")
            except Exception:
                pass

        # Python
        elif "requirements.txt" in files or "pyproject.toml" in files or "Pipfile" in files:
            language = "Python"
            build_tool = "pip"
            req_content = cls._read_file_safe(os.path.join(dir_path, "requirements.txt")) or cls._read_file_safe(os.path.join(dir_path, "pyproject.toml"))
            if "fastapi" in req_content.lower():
                framework = "FastAPI"
            elif "django" in req_content.lower():
                framework = "Django"
            elif "flask" in req_content.lower():
                framework = "Flask"
            
            if "psycopg" in req_content.lower() or "asyncpg" in req_content.lower():
                databases.append("PostgreSQL")
            if "redis" in req_content.lower():
                databases.append("Redis")
            if "celery" in req_content.lower():
                queues.append("Celery")

        # Go
        elif "go.mod" in files:
            language = "Go"
            build_tool = "Go Modules"
            go_content = cls._read_file_safe(os.path.join(dir_path, "go.mod"))
            if "gin-gonic" in go_content:
                framework = "Gin"
            elif "echo" in go_content:
                framework = "Echo"

        # Rust
        elif "Cargo.toml" in files:
            language = "Rust"
            build_tool = "Cargo"
            cargo_content = cls._read_file_safe(os.path.join(dir_path, "Cargo.toml"))
            if "actix" in cargo_content:
                framework = "Actix-web"
            elif "axum" in cargo_content:
                framework = "Axum"

        # Dockerfile checks & port extraction
        has_dockerfile = "Dockerfile" in files
        if has_dockerfile:
            df_content = cls._read_file_safe(os.path.join(dir_path, "Dockerfile"))
            expose_match = re.findall(r"EXPOSE\s+(\d+)", df_content, re.IGNORECASE)
            for p in expose_match:
                try:
                    ports.append(int(p))
                except ValueError:
                    pass

        # Also check application.properties or application.yml for server.port
        for root, _, fs in os.walk(dir_path):
            for f in fs:
                if f in ["application.properties", "application.yml", "application.yaml"]:
                    cfg = cls._read_file_safe(os.path.join(root, f))
                    port_match = re.search(r"server\.port\s*[:=]\s*(\d+)", cfg)
                    if port_match:
                        try:
                            ports.append(int(port_match.group(1)))
                        except ValueError:
                            pass

        if language == "Unknown" and not has_dockerfile:
            return None

        return {
            "service_id": name.lower().replace("_", "-"),
            "service_name": name,
            "language": language,
            "framework": framework,
            "build_tool": build_tool,
            "databases": list(set(databases)),
            "queues": list(set(queues)),
            "ports": list(set(ports)),
            "has_dockerfile": has_dockerfile,
            "tests_found": any("test" in f.lower() for f in files) or os.path.exists(os.path.join(dir_path, "src", "test"))
        }

    @classmethod
    def _classify_architecture(cls, root_path: str, services: List[Dict[str, Any]]) -> str:
        if len(services) > 1:
            # Check if docker-compose defines microservice cluster
            if os.path.exists(os.path.join(root_path, "docker-compose.yml")) or os.path.exists(os.path.join(root_path, "docker-compose.yaml")):
                return "MICROSERVICES"
            return "MONOREPO"
        elif len(services) == 1:
            srv = services[0]
            if srv["relative_path"] == ".":
                return "SINGLE_APPLICATION"
            return "MODULAR_MONOLITH"
        return "SINGLE_APPLICATION"

    @classmethod
    def _build_service_graph(cls, root_path: str, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        nodes = []
        edges = []
        dependencies: Dict[str, List[str]] = {}

        service_names = {s["service_id"]: s for s in services}

        # Create nodes for services
        for s in services:
            nodes.append({
                "id": s["service_id"],
                "name": s["service_name"],
                "type": "service",
                "language": s["language"],
                "framework": s["framework"],
                "ports": s["ports"]
            })
            dependencies[s["service_id"]] = []

            # Add connected databases as resource nodes
            for db in s.get("databases", []):
                db_id = f"db-{db.lower()}"
                if not any(n["id"] == db_id for n in nodes):
                    nodes.append({"id": db_id, "name": db, "type": "database"})
                edges.append({
                    "source": s["service_id"],
                    "target": db_id,
                    "type": "database_access",
                    "protocol": "SQL/TCP"
                })

            # Add queues
            for q in s.get("queues", []):
                q_id = f"queue-{q.lower()}"
                if not any(n["id"] == q_id for n in nodes):
                    nodes.append({"id": q_id, "name": q, "type": "queue"})
                edges.append({
                    "source": s["service_id"],
                    "target": q_id,
                    "type": "event_stream",
                    "protocol": "ASYNC"
                })

        # Scan code for cross-service calls (e.g. FeignClient, RestTemplate, WebClient, fetch, axios, http)
        for s in services:
            srv_dir = os.path.join(root_path, s["relative_path"])
            if not os.path.exists(srv_dir):
                continue
            
            for r, _, fs in os.walk(srv_dir):
                for f in fs:
                    if f.endswith((".java", ".ts", ".js", ".py", ".go", ".rs")):
                        content = cls._read_file_safe(os.path.join(r, f))
                        for target_id, target_srv in service_names.items():
                            if target_id == s["service_id"]:
                                continue
                            # Look for service name or ports in HTTP client calls
                            if (target_srv["service_name"].lower() in content.lower() or 
                                any(str(p) in content for p in target_srv.get("ports", [])) or
                                f"http://{target_id}" in content or f"http://{target_srv['service_name']}" in content):
                                if target_id not in dependencies[s["service_id"]]:
                                    dependencies[s["service_id"]].append(target_id)
                                    edges.append({
                                        "source": s["service_id"],
                                        "target": target_id,
                                        "type": "http_request",
                                        "protocol": "REST/JSON"
                                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "dependencies": dependencies
        }

    @classmethod
    def _index_symbols_and_endpoints(cls, root_path: str, services: List[Dict[str, Any]]) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        symbols: Dict[str, Any] = {}
        endpoints: List[Dict[str, Any]] = []

        for s in services:
            srv_id = s["service_id"]
            symbols[srv_id] = {"classes": [], "methods": [], "controllers": []}
            srv_dir = os.path.join(root_path, s["relative_path"])
            if not os.path.exists(srv_dir):
                continue

            for r, _, fs in os.walk(srv_dir):
                for f in fs:
                    if f.endswith((".java", ".py", ".ts", ".js", ".go")):
                        rel_file = os.path.relpath(os.path.join(r, f), root_path).replace("\\", "/")
                        content = cls._read_file_safe(os.path.join(r, f))
                        
                        # Extract classes
                        for c in re.findall(r"class\s+([A-Za-z0-9_]+)", content):
                            symbols[srv_id]["classes"].append({"name": c, "file": rel_file})

                        # Extract endpoints (Java Spring, FastAPI, Express)
                        for m in re.findall(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*["\']([^"\']+)["\']', content):
                            method = m[0].replace("Mapping", "").upper() if m[0] != "RequestMapping" else "ALL"
                            endpoints.append({
                                "service_id": srv_id,
                                "method": method,
                                "path": m[1],
                                "file": rel_file
                            })
                        for m in re.findall(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
                            endpoints.append({
                                "service_id": srv_id,
                                "method": m[0].upper(),
                                "path": m[1],
                                "file": rel_file
                            })

        return symbols, endpoints

    @classmethod
    def _extract_configuration_manifest(cls, root_path: str, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        config_items: List[Dict[str, Any]] = []
        seen_keys = set()

        for s in services:
            srv_id = s["service_id"]
            srv_dir = os.path.join(root_path, s["relative_path"])
            if not os.path.exists(srv_dir):
                continue

            # Find .env.example, application.yml, etc.
            for r, _, fs in os.walk(srv_dir):
                for f in fs:
                    full_p = os.path.join(r, f)
                    rel_p = os.path.relpath(full_p, root_path).replace("\\", "/")
                    
                    if f in [".env.example", ".env.template", ".env.sample"]:
                        content = cls._read_file_safe(full_p)
                        for line in content.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k = line.split("=", 1)[0].strip()
                                if (srv_id, k) not in seen_keys:
                                    seen_keys.add((srv_id, k))
                                    config_items.append({
                                        "service_id": srv_id,
                                        "key": k,
                                        "source_file": rel_p,
                                        "required": True,
                                        "category": "environment"
                                    })
                    elif f.endswith((".properties", ".yml", ".yaml")):
                        content = cls._read_file_safe(full_p)
                        # Extract env var placeholders like ${PAYMENT_TIMEOUT:3000}
                        for match in re.findall(r'\$\{([A-Z0-9_]+)(?::[^}]+)?\}', content):
                            if (srv_id, match) not in seen_keys:
                                seen_keys.add((srv_id, match))
                                config_items.append({
                                    "service_id": srv_id,
                                    "key": match,
                                    "source_file": rel_p,
                                    "required": True,
                                    "category": "spring_config"
                                })

        return config_items

    @classmethod
    def _read_file_safe(cls, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    @classmethod
    def _empty_intelligence(cls) -> Dict[str, Any]:
        return {
            "architecture_type": "SINGLE_APPLICATION",
            "services_inventory": [],
            "service_graph": {"nodes": [], "edges": [], "dependencies": {}},
            "dependency_graph": {},
            "symbol_index": {},
            "endpoint_index": [],
            "config_manifest": [],
            "commit_sha": "HEAD",
            "analyzed_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def ensure_index_persisted(cls, db, repo_path: str, repository_id, commit_sha: str):
        from app.db.models import RepositoryIntelligence
        import uuid
        
        existing = db.query(RepositoryIntelligence).filter(
            RepositoryIntelligence.repository_id == repository_id,
            RepositoryIntelligence.commit_sha == commit_sha
        ).first()

        if existing:
            logger.info(f"RepositoryIntelligence already exists for repo {repository_id} commit {commit_sha}")
            return existing

        logger.info(f"Generating new RepositoryIntelligence for repo {repository_id} commit {commit_sha}")
        intelligence = cls.analyze_repository(repo_path, commit_sha)
        
        new_index = RepositoryIntelligence(
            id=uuid.uuid4(),
            repository_id=repository_id,
            commit_sha=commit_sha,
            architecture_type=intelligence.get("architecture_type", "SINGLE_APPLICATION"),
            services_inventory=intelligence.get("services_inventory", []),
            service_graph=intelligence.get("service_graph", {}),
            dependency_graph=intelligence.get("dependency_graph", {}),
            symbol_index=intelligence.get("symbol_index", {}),
            endpoint_index=intelligence.get("endpoint_index", []),
            config_manifest=intelligence.get("config_manifest", []),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_index)
        db.commit()
        db.refresh(new_index)
        return new_index
