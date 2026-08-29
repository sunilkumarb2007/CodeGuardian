from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Run
from app.services.capsule_service import CapsuleService
import uuid

router = APIRouter()


@router.get("/runs/{run_id}/capsule")
def download_capsule(run_id: str, db: Session = Depends(get_db)):
    """
    Downloads a sealed, sanitized Failure Capsule zip archive.
    """
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.incident_id:
        incident_id = uuid.uuid4()
    else:
        incident_id = run.incident_id

    svc = CapsuleService(db)
    capsule_data = svc.generate_capsule(incident_id=incident_id, run_id=run_id)

    headers = {
        "Content-Disposition": f"attachment; filename=codeguardian-capsule-{run_id[:8]}.zip"
    }
    return Response(
        content=capsule_data["zip_bytes"],
        media_type="application/zip",
        headers=headers,
    )


@router.post("/capsules/import")
async def import_capsule(request: Request, db: Session = Depends(get_db)):
    """
    Validates and imports an untrusted Failure Capsule archive.
    """
    contents = await request.body()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty capsule payload.")
    svc = CapsuleService(db)
    try:
        result = svc.validate_and_import(contents)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
