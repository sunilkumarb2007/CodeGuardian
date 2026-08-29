from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class RepositoryTechnology(BaseModel):
    language: Optional[str] = None
    framework: Optional[str] = None
    build_system: Optional[str] = None
    test_system: Optional[str] = None

class RepositoryTreeNode(BaseModel):
    name: str
    type: str
    children: Optional[List['RepositoryTreeNode']] = None

class RepositoryAnalysisResponse(BaseModel):
    id: str
    owner: str
    name: str
    url: str
    default_branch: str
    technology: RepositoryTechnology
    tree: RepositoryTreeNode
    status: str

class RepositoryConnectionCreate(BaseModel):
    provider: Optional[str] = "github"
    owner: str
    name: str
    repository_url: str
    default_branch: Optional[str] = "main"
    monitoring_enabled: Optional[bool] = True
    automatic_investigation_enabled: Optional[bool] = True
    auto_pr_enabled: Optional[bool] = False
    approval_policy: Optional[str] = "HUMAN_APPROVAL_REQUIRED"
    notification_policy: Optional[Dict[str, Any]] = {"email": True, "whatsapp": False, "in_app": True}
    webhook_secret: Optional[str] = None

class RepositoryConnectionUpdate(BaseModel):
    monitoring_enabled: Optional[bool] = None
    automatic_investigation_enabled: Optional[bool] = None
    auto_pr_enabled: Optional[bool] = None
    approval_policy: Optional[str] = None
    notification_policy: Optional[Dict[str, Any]] = None
    default_branch: Optional[str] = None

class RepositoryConnectionResponse(BaseModel):
    id: UUID
    repository_id: Optional[UUID] = None
    provider: str
    owner: str
    name: str
    repository_url: str
    default_branch: str
    monitoring_enabled: bool
    automatic_investigation_enabled: bool
    auto_pr_enabled: bool
    approval_policy: str
    notification_policy: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

