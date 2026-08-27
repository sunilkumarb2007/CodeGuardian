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
