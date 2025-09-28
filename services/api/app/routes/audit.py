"""Audit log endpoints."""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..models import AuditLog
from ..utils import require_membership

router = APIRouter(prefix="/workspaces/{workspace_id:int}", tags=["audit"])


@router.get("/audit", response_model=List[schemas.AuditLogOut])
def list_audit_logs(
    workspace_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[schemas.AuditLogOut]:
    """Return recent audit log events for the workspace."""

    require_membership(db, user.id, workspace_id)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.AuditLogOut(
            id=log.id,
            workspace_id=log.workspace_id,
            user_id=log.user_id,
            action=log.action,
            meta=log.meta or {},
            created_at=log.created_at,
        )
        for log in logs
    ]
