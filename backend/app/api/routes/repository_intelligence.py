from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.repository_intelligence_service import RepositoryIntelligenceService

router = APIRouter(prefix="/api/intelligence", tags=["Repository Intelligence"])

class AnalyzeRepoRequest(BaseModel):
    repository_path: str
    commit_sha: Optional[str] = None

@router.post("/analyze")
def analyze_repository(req: AnalyzeRepoRequest):
    """
    Analyzes repository architecture, discovering microservices, dependency graphs,
    symbol indices, and configuration manifests.
    """
    try:
        data = RepositoryIntelligenceService.analyze_repository(req.repository_path, req.commit_sha)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
