from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.config_guardian_service import ConfigurationGuardianService

router = APIRouter(prefix="/api/config-guardian", tags=["Configuration Guardian"])

class AuditConfigRequest(BaseModel):
    repository_path: str
    service_path: str
    service_name: str
    observed_env_keys: Optional[Dict[str, str]] = None  # Key names only

@router.post("/audit")
def audit_configuration(req: AuditConfigRequest):
    """
    Audits configuration drift, missing keys, and schema requirements.
    Guaranteed zero plaintext secret exposure.
    """
    try:
        res = ConfigurationGuardianService.audit_service_configuration(
            repo_path=req.repository_path,
            service_path=req.service_path,
            service_name=req.service_name,
            observed_env=req.observed_env_keys
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration audit failed: {str(e)}")
