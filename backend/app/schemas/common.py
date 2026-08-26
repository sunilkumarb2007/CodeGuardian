from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    service: str

class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
