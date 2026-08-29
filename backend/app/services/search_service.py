import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from app.db.models import (
    RepositoryIntelligence, 
    RepositoryFile, 
    Incident, 
    FailureMemory,
    EvidenceEvent
)

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query: str,
        repository_id: Optional[uuid.UUID] = None,
        commit_sha: Optional[str] = None,
        search_type: str = "all",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fast deterministic search across indexed entities.
        Does not invoke AI. Ranks results based on exact match and type.
        """
        results = []
        q_lower = query.lower()

        # 1. Search Repository Intelligence (Symbols, Services, Endpoints, Configs)
        if repository_id:
            # Find the most recent or specific index
            idx_query = self.db.query(RepositoryIntelligence).filter(
                RepositoryIntelligence.repository_id == repository_id
            )
            if commit_sha:
                idx_query = idx_query.filter(RepositoryIntelligence.commit_sha == commit_sha)
            
            intelligence = idx_query.order_by(RepositoryIntelligence.created_at.desc()).first()

            if intelligence:
                # Services
                if search_type in ["all", "service"]:
                    for srv in intelligence.services_inventory:
                        if q_lower in srv.get("service_name", "").lower() or q_lower in srv.get("service_id", "").lower():
                            results.append({
                                "type": "service",
                                "id": srv.get("service_id"),
                                "title": srv.get("service_name"),
                                "subtitle": f"Framework: {srv.get('framework', 'Unknown')}",
                                "language": srv.get("language"),
                                "path": srv.get("relative_path"),
                                "relevance": 4
                            })

                # Symbols
                if search_type in ["all", "symbol"]:
                    symbols_dict = intelligence.symbol_index
                    for srv_id, sym_data in symbols_dict.items():
                        for kind in ["classes", "methods", "controllers"]:
                            for sym in sym_data.get(kind, []):
                                if q_lower in sym.get("name", "").lower():
                                    results.append({
                                        "type": "symbol",
                                        "id": f"{srv_id}-{sym.get('name')}",
                                        "title": sym.get("name"),
                                        "subtitle": f"{kind[:-2].capitalize()} in {srv_id}",
                                        "service": srv_id,
                                        "path": sym.get("file"),
                                        "relevance": 3
                                    })

                # Endpoints
                if search_type in ["all", "endpoint"]:
                    for ep in intelligence.endpoint_index:
                        if q_lower in ep.get("path", "").lower() or q_lower in ep.get("method", "").lower():
                            results.append({
                                "type": "endpoint",
                                "id": f"{ep.get('service_id')}-{ep.get('method')}-{ep.get('path')}",
                                "title": f"{ep.get('method')} {ep.get('path')}",
                                "subtitle": f"Endpoint in {ep.get('service_id')}",
                                "service": ep.get("service_id"),
                                "path": ep.get("file"),
                                "relevance": 5
                            })

                # Configs
                if search_type in ["all", "config"]:
                    for cfg in intelligence.config_manifest:
                        if q_lower in cfg.get("key", "").lower():
                            results.append({
                                "type": "config",
                                "id": f"{cfg.get('service_id')}-{cfg.get('key')}",
                                "title": cfg.get("key"),
                                "subtitle": f"Config in {cfg.get('source_file')}",
                                "service": cfg.get("service_id"),
                                "path": cfg.get("source_file"),
                                "relevance": 5
                            })

            # Files
            if search_type in ["all", "file"]:
                files = self.db.query(RepositoryFile).filter(
                    RepositoryFile.repository_id == repository_id,
                    RepositoryFile.file_path.ilike(f"%{q_lower}%")
                ).limit(limit).all()
                for f in files:
                    results.append({
                        "type": "file",
                        "id": str(f.id),
                        "title": f.file_path.split("/")[-1],
                        "subtitle": f.file_path,
                        "path": f.file_path,
                        "relevance": 5
                    })

        # 2. Search Incidents / Failures
        if search_type in ["all", "incident", "failure"]:
            inc_query = self.db.query(Incident).filter(
                or_(
                    Incident.title.ilike(f"%{q_lower}%"),
                    Incident.error_fingerprint.ilike(f"%{q_lower}%"),
                    Incident.root_cause_service.ilike(f"%{q_lower}%")
                )
            )
            if repository_id:
                inc_query = inc_query.filter(Incident.repository_id == repository_id)
                
            incidents = inc_query.limit(10).all()
            for inc in incidents:
                results.append({
                    "type": "incident",
                    "id": str(inc.id),
                    "title": inc.title,
                    "subtitle": f"Incident {inc.incident_number} - {inc.status}",
                    "service": inc.root_cause_service,
                    "relevance": 2 if q_lower in (inc.error_fingerprint or "").lower() else 4
                })

        # 3. Search Failure Memory
        if search_type in ["all", "memory"]:
            mem_query = self.db.query(FailureMemory).filter(
                or_(
                    FailureMemory.error_pattern.ilike(f"%{q_lower}%"),
                    FailureMemory.root_cause.ilike(f"%{q_lower}%"),
                    FailureMemory.searchable_text.ilike(f"%{q_lower}%")
                )
            ).limit(10).all()
            for mem in mem_query:
                results.append({
                    "type": "memory",
                    "id": str(mem.id),
                    "title": "Historical Repair",
                    "subtitle": mem.error_pattern[:50] + "...",
                    "relevance": 3
                })

        # Rank results
        results.sort(key=lambda x: x.get("relevance", 99))
        return results[:limit]
