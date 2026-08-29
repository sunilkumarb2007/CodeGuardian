from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.companion_service import CompanionService

router = APIRouter(prefix="/api/companion", tags=["CodeGuardian Companion"])

class ContextPackRequest(BaseModel):
    repository_path: str
    scope_type: str = "service"
    target_path: Optional[str] = None
    selected_code: Optional[str] = None
    symbol_name: Optional[str] = None
    stack_trace: Optional[str] = None

class ExplainRequest(BaseModel):
    context_pack: Dict[str, Any]
    symbol_name: Optional[str] = None

@router.post("/context")
def assemble_context(req: ContextPackRequest):
    """
    Assembles a minimal, bounded ContextPack for VS Code, CLI, and Web clients.
    """
    try:
        pack = CompanionService.assemble_context_pack(
            repo_path=req.repository_path,
            scope_type=req.scope_type,
            target_path=req.target_path,
            selected_code=req.selected_code,
            symbol_name=req.symbol_name,
            stack_trace=req.stack_trace
        )
        return pack
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assemble context: {str(e)}")

@router.post("/explain")
def explain_code(req: ExplainRequest):
    """
    Explains selected function or code segment without making modifications.
    """
    try:
        res = CompanionService.explain_code(req.context_pack, req.symbol_name)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explain failed: {str(e)}")
