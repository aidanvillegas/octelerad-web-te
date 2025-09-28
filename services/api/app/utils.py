"""Utility helpers for workspace membership and snippet responses."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .metrics import SNIPPET_MUTATIONS
from .models import Membership, Snippet, SnippetVersion
from .schemas import SnippetOut


def require_membership(
    db: Session,
    user_id: int,
    workspace_id: int,
    roles: Optional[list[str]] = None,
) -> Membership:
    membership = (
        db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.workspace_id == workspace_id,
            )
        )
        .scalars()
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")
    if roles and membership.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return membership


def serialize_snippet(snippet: Snippet, version: Optional[int] = None) -> SnippetOut:
    """Return a `SnippetOut` for the supplied snippet."""

    latest_version = version
    if latest_version is None:
        latest_version = (
            max((v.version for v in snippet.versions), default=1)
            if snippet.versions
            else 1
        )
    updated_at = snippet.updated_at or datetime.utcnow()
    return SnippetOut(
        id=snippet.id,
        name=snippet.name,
        trigger=snippet.trigger,
        body=snippet.body,
        tags=snippet.tags or [],
        variables=snippet.variables or {},
        version=latest_version,
        updated_at=updated_at,
    )


def record_snippet_mutation(action: str) -> None:
    """Increment metrics counter for snippet mutations."""

    SNIPPET_MUTATIONS.labels(action=action).inc()
