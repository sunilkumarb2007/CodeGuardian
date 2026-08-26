from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.schemas.common import HealthResponse, DatabaseHealthResponse

router = APIRouter()

@router.get("", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "service": "CodeGuardian"}

@router.get("/database", response_model=DatabaseHealthResponse)
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database connection failed")
