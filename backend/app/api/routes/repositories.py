from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from app.db.database import get_db
from app.db import models
from app.schemas.repository import (
    RepositoryConnectionCreate,
    RepositoryConnectionUpdate,
    RepositoryConnectionResponse,
)

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.post("/connect", response_model=RepositoryConnectionResponse, status_code=status.HTTP_201_CREATED)
def connect_repository(
    payload: RepositoryConnectionCreate,
    db: Session = Depends(get_db)
):
    """
    Phase 1: Connect Repository.
    Registers a repository with monitoring, investigation, and approval policies.
    """
    # 1. Ensure application exists
    app = db.query(models.Application).first()
    if not app:
        app = models.Application(
            id=uuid.uuid4(),
            name="CodeGuardian",
            environment="production",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(app)
        db.flush()

    # 2. Check if Repository already exists
    repo = (
        db.query(models.Repository)
        .filter(
            models.Repository.owner == payload.owner,
            models.Repository.name == payload.name
        )
        .first()
    )

    now = datetime.now(timezone.utc)

    if not repo:
        repo = models.Repository(
            id=uuid.uuid4(),
            application_id=app.id,
            provider=payload.provider or "github",
            owner=payload.owner,
            name=payload.name,
            repository_url=payload.repository_url,
            default_branch=payload.default_branch or "main",
            access_status="CONNECTED",
            created_at=now,
            updated_at=now,
        )
        db.add(repo)
        db.flush()

    # 3. Check or create RepositoryConnection
    conn = (
        db.query(models.RepositoryConnection)
        .filter(models.RepositoryConnection.repository_id == repo.id)
        .first()
    )

    if not conn:
        conn = models.RepositoryConnection(
            id=uuid.uuid4(),
            repository_id=repo.id,
            provider=payload.provider or "github",
            owner=payload.owner,
            name=payload.name,
            repository_url=payload.repository_url,
            default_branch=payload.default_branch or "main",
            monitoring_enabled=payload.monitoring_enabled if payload.monitoring_enabled is not None else True,
            automatic_investigation_enabled=payload.automatic_investigation_enabled if payload.automatic_investigation_enabled is not None else True,
            auto_pr_enabled=payload.auto_pr_enabled if payload.auto_pr_enabled is not None else False,
            approval_policy=payload.approval_policy or "HUMAN_APPROVAL_REQUIRED",
            notification_policy=payload.notification_policy or {"email": True, "whatsapp": False, "in_app": True},
            webhook_secret=payload.webhook_secret,
            created_at=now,
            updated_at=now,
        )
        db.add(conn)
    else:
        conn.monitoring_enabled = payload.monitoring_enabled if payload.monitoring_enabled is not None else conn.monitoring_enabled
        conn.automatic_investigation_enabled = payload.automatic_investigation_enabled if payload.automatic_investigation_enabled is not None else conn.automatic_investigation_enabled
        conn.auto_pr_enabled = payload.auto_pr_enabled if payload.auto_pr_enabled is not None else conn.auto_pr_enabled
        conn.approval_policy = payload.approval_policy or conn.approval_policy
        conn.notification_policy = payload.notification_policy or conn.notification_policy
        conn.updated_at = now

    db.commit()
    db.refresh(conn)

    return RepositoryConnectionResponse(
        id=conn.id,
        repository_id=conn.repository_id,
        provider=conn.provider,
        owner=conn.owner,
        name=conn.name,
        repository_url=conn.repository_url,
        default_branch=conn.default_branch,
        monitoring_enabled=conn.monitoring_enabled,
        automatic_investigation_enabled=conn.automatic_investigation_enabled,
        auto_pr_enabled=conn.auto_pr_enabled,
        approval_policy=conn.approval_policy,
        notification_policy=conn.notification_policy or {},
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


@router.get("/connections", response_model=List[RepositoryConnectionResponse])
def list_connections(db: Session = Depends(get_db)):
    """
    List all connected repositories.
    """
    conns = db.query(models.RepositoryConnection).order_by(models.RepositoryConnection.created_at.desc()).all()
    return [
        RepositoryConnectionResponse(
            id=c.id,
            repository_id=c.repository_id,
            provider=c.provider,
            owner=c.owner,
            name=c.name,
            repository_url=c.repository_url,
            default_branch=c.default_branch,
            monitoring_enabled=c.monitoring_enabled,
            automatic_investigation_enabled=c.automatic_investigation_enabled,
            auto_pr_enabled=c.auto_pr_enabled,
            approval_policy=c.approval_policy,
            notification_policy=c.notification_policy or {},
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in conns
    ]


@router.get("/{repository_id}/connection", response_model=RepositoryConnectionResponse)
def get_connection(repository_id: UUID, db: Session = Depends(get_db)):
    """
    Get repository connection settings.
    """
    conn = (
        db.query(models.RepositoryConnection)
        .filter(
            (models.RepositoryConnection.repository_id == repository_id) |
            (models.RepositoryConnection.id == repository_id)
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Repository connection not found")

    return RepositoryConnectionResponse(
        id=conn.id,
        repository_id=conn.repository_id,
        provider=conn.provider,
        owner=conn.owner,
        name=conn.name,
        repository_url=conn.repository_url,
        default_branch=conn.default_branch,
        monitoring_enabled=conn.monitoring_enabled,
        automatic_investigation_enabled=conn.automatic_investigation_enabled,
        auto_pr_enabled=conn.auto_pr_enabled,
        approval_policy=conn.approval_policy,
        notification_policy=conn.notification_policy or {},
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


@router.patch("/{repository_id}/connection", response_model=RepositoryConnectionResponse)
def update_connection(
    repository_id: UUID,
    payload: RepositoryConnectionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update repository connection settings.
    """
    conn = (
        db.query(models.RepositoryConnection)
        .filter(
            (models.RepositoryConnection.repository_id == repository_id) |
            (models.RepositoryConnection.id == repository_id)
        )
        .first()
    )
    if not conn:
        raise HTTPException(status_code=404, detail="Repository connection not found")

    if payload.monitoring_enabled is not None:
        conn.monitoring_enabled = payload.monitoring_enabled
    if payload.automatic_investigation_enabled is not None:
        conn.automatic_investigation_enabled = payload.automatic_investigation_enabled
    if payload.auto_pr_enabled is not None:
        conn.auto_pr_enabled = payload.auto_pr_enabled
    if payload.approval_policy is not None:
        conn.approval_policy = payload.approval_policy
    if payload.notification_policy is not None:
        conn.notification_policy = payload.notification_policy
    if payload.default_branch is not None:
        conn.default_branch = payload.default_branch

    conn.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conn)

    return RepositoryConnectionResponse(
        id=conn.id,
        repository_id=conn.repository_id,
        provider=conn.provider,
        owner=conn.owner,
        name=conn.name,
        repository_url=conn.repository_url,
        default_branch=conn.default_branch,
        monitoring_enabled=conn.monitoring_enabled,
        automatic_investigation_enabled=conn.automatic_investigation_enabled,
        auto_pr_enabled=conn.auto_pr_enabled,
        approval_policy=conn.approval_policy,
        notification_policy=conn.notification_policy or {},
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )
