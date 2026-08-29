from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
import uuid

from app.db.database import get_db
from app.services.search_service import SearchService

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def search(
    q: str = Query(..., min_length=1),
    repository_id: Optional[uuid.UUID] = None,
    commit_sha: Optional[str] = None,
    type: str = Query("all", description="Type of search: all, symbol, file, endpoint, service, config, incident, memory"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Unified deterministic search endpoint for Repository Intelligence, Incidents, and Memory.
    No AI is invoked. Fast exact/fuzzy matching across the DB.
    """
    search_service = SearchService(db)
    
    try:
        results = search_service.search(
            query=q,
            repository_id=repository_id,
            commit_sha=commit_sha,
            search_type=type,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
