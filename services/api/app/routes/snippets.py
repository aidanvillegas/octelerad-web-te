"""Snippet-related endpoints for the Macro Library API."""

from datetime import datetime
import json
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..models import AuditLog, Snippet, SnippetVersion
from ..utils import record_snippet_mutation, require_membership, serialize_snippet

router = APIRouter(prefix="/workspaces/{workspace_id:int}", tags=["snippets"])


@router.get("/snippets", response_model=List[schemas.SnippetOut])
def list_snippets(
    workspace_id: int,
    q: str | None = Query(default=None, description="Optional search query"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[schemas.SnippetOut]:
    """Return snippets for a workspace with optional fuzzy search."""

    require_membership(db, user.id, workspace_id)
    query = db.query(Snippet).filter(Snippet.workspace_id == workspace_id, Snippet.is_archived.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Snippet.name.ilike(like), Snippet.trigger.ilike(like), Snippet.body.ilike(like)))
    snippets = query.order_by(Snippet.updated_at.desc()).all()
    return [serialize_snippet(snippet) for snippet in snippets]


@router.post("/snippets", response_model=schemas.SnippetOut, status_code=status.HTTP_201_CREATED)
def create_snippet(
    workspace_id: int,
    payload: schemas.SnippetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Create a new snippet and its first version."""

    require_membership(db, user.id, workspace_id, roles=["admin", "editor"])
    existing = (
        db.query(Snippet)
        .filter(Snippet.workspace_id == workspace_id, Snippet.trigger == payload.trigger)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trigger already exists")

    snippet = Snippet(
        workspace_id=workspace_id,
        name=payload.name,
        trigger=payload.trigger,
        body=payload.body,
        tags=payload.tags,
        variables=payload.variables,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(snippet)
    db.flush()

    version = SnippetVersion(
        snippet_id=snippet.id,
        version=1,
        name=snippet.name,
        trigger=snippet.trigger,
        body=snippet.body,
        tags=snippet.tags,
        variables=snippet.variables,
        edited_by=user.id,
    )
    db.add(version)
    db.add(
        AuditLog(
            workspace_id=workspace_id,
            user_id=user.id,
            action="create_snippet",
            meta={"snippet_id": snippet.id},
        )
    )
    db.commit()
    db.refresh(snippet)
    record_snippet_mutation("create")
    return serialize_snippet(snippet, version=1)


@router.put("/snippets/{snippet_id:int}", response_model=schemas.SnippetOut)
def update_snippet(
    workspace_id: int,
    snippet_id: int,
    payload: schemas.SnippetUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Update a snippet and append a new version."""

    require_membership(db, user.id, workspace_id, roles=["admin", "editor"])
    snippet = (
        db.query(Snippet)
        .filter(Snippet.id == snippet_id, Snippet.workspace_id == workspace_id)
        .first()
    )
    if snippet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snippet not found")

    last_version = (
        db.query(SnippetVersion)
        .filter(SnippetVersion.snippet_id == snippet.id)
        .order_by(SnippetVersion.version.desc())
        .first()
    )
    next_version = (last_version.version if last_version else 0) + 1

    snippet.name = payload.name
    snippet.trigger = payload.trigger
    snippet.body = payload.body
    snippet.tags = payload.tags
    snippet.variables = payload.variables
    snippet.updated_by = user.id

    db.add(
        SnippetVersion(
            snippet_id=snippet.id,
            version=next_version,
            name=snippet.name,
            trigger=snippet.trigger,
            body=snippet.body,
            tags=snippet.tags,
            variables=snippet.variables,
            edited_by=user.id,
        )
    )
    db.add(
        AuditLog(
            workspace_id=workspace_id,
            user_id=user.id,
            action="update_snippet",
            meta={"snippet_id": snippet.id, "version": next_version},
        )
    )
    db.commit()
    db.refresh(snippet)
    record_snippet_mutation("update")
    return serialize_snippet(snippet, version=next_version)


@router.post("/snippets/{snippet_id:int}/restore/{version:int}", response_model=schemas.SnippetOut)
def restore_snippet_version(
    workspace_id: int,
    snippet_id: int,
    version: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Restore a snippet to a previous version (records a new version)."""

    require_membership(db, user.id, workspace_id, roles=["admin", "editor"])
    snippet = (
        db.query(Snippet)
        .filter(Snippet.id == snippet_id, Snippet.workspace_id == workspace_id)
        .first()
    )
    if snippet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snippet not found")

    version_row = (
        db.query(SnippetVersion)
        .filter(SnippetVersion.snippet_id == snippet.id, SnippetVersion.version == version)
        .first()
    )
    if version_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    last_version = (
        db.query(SnippetVersion)
        .filter(SnippetVersion.snippet_id == snippet.id)
        .order_by(SnippetVersion.version.desc())
        .first()
    )
    next_version = (last_version.version if last_version else 0) + 1

    snippet.name = version_row.name
    snippet.trigger = version_row.trigger
    snippet.body = version_row.body
    snippet.tags = version_row.tags
    snippet.variables = version_row.variables
    snippet.updated_by = user.id

    db.add(
        SnippetVersion(
            snippet_id=snippet.id,
            version=next_version,
            name=snippet.name,
            trigger=snippet.trigger,
            body=snippet.body,
            tags=snippet.tags,
            variables=snippet.variables,
            edited_by=user.id,
        )
    )
    db.add(
        AuditLog(
            workspace_id=workspace_id,
            user_id=user.id,
            action="restore_version",
            meta={"snippet_id": snippet.id, "to_version": next_version, "from_version": version},
        )
    )
    db.commit()
    db.refresh(snippet)
    record_snippet_mutation("restore")
    return serialize_snippet(snippet, version=next_version)


@router.get("/snippets/since", response_model=List[schemas.SnippetDelta])
def snippets_since(
    workspace_id: int,
    since_ts: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[schemas.SnippetDelta]:
    """Return snippets updated after the provided ISO timestamp."""

    require_membership(db, user.id, workspace_id)
    try:
        dt = datetime.fromisoformat(since_ts.replace("Z", ""))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp") from exc

    snippets = (
        db.query(Snippet)
        .filter(
            Snippet.workspace_id == workspace_id,
            Snippet.updated_at > dt,
            Snippet.is_archived.is_(False),
        )
        .order_by(Snippet.updated_at.asc())
        .all()
    )
    return [serialize_snippet(snippet) for snippet in snippets]


@router.get("/export")
def export_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Export snippets as JSON payload."""

    require_membership(db, user.id, workspace_id)
    snippets = (
        db.query(Snippet)
        .filter(Snippet.workspace_id == workspace_id, Snippet.is_archived.is_(False))
        .all()
    )

    payload = {
        "schema": "text-expander.v1",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "workspace_id": workspace_id,
        "snippets": [
            {
                "name": s.name,
                "trigger": s.trigger,
                "body": s.body,
                "tags": s.tags or [],
                "variables": s.variables or {},
                "updated_at": (s.updated_at or datetime.utcnow()).isoformat() + "Z",
            }
            for s in snippets
        ],
    }

    db.add(
        AuditLog(
            workspace_id=workspace_id,
            user_id=user.id,
            action="export",
            meta={"count": len(payload["snippets"])}
        )
    )
    db.commit()
    record_snippet_mutation("export")
    return payload


@router.post("/import")
def import_workspace(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Import snippets from a JSON payload."""

    require_membership(db, user.id, workspace_id, roles=["admin", "editor"])
    data = json.loads(file.file.read().decode("utf-8"))
    if data.get("schema") != "text-expander.v1":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported schema")

    imported = 0
    for snippet_data in data.get("snippets", []):
        trigger = snippet_data["trigger"]
        snippet = (
            db.query(Snippet)
            .filter(Snippet.workspace_id == workspace_id, Snippet.trigger == trigger)
            .first()
        )
        if snippet is None:
            snippet = Snippet(
                workspace_id=workspace_id,
                name=snippet_data["name"],
                trigger=trigger,
                body=snippet_data["body"],
                tags=snippet_data.get("tags", []),
                variables=snippet_data.get("variables", {}),
                created_by=user.id,
                updated_by=user.id,
            )
            db.add(snippet)
            db.flush()
            version_number = 1
        else:
            version_row = (
                db.query(SnippetVersion)
                .filter(SnippetVersion.snippet_id == snippet.id)
                .order_by(SnippetVersion.version.desc())
                .first()
            )
            version_number = (version_row.version if version_row else 0) + 1
            snippet.name = snippet_data["name"]
            snippet.body = snippet_data["body"]
            snippet.tags = snippet_data.get("tags", [])
            snippet.variables = snippet_data.get("variables", {})
            snippet.updated_by = user.id

        db.add(
            SnippetVersion(
                snippet_id=snippet.id,
                version=version_number,
                name=snippet.name,
                trigger=snippet.trigger,
                body=snippet.body,
                tags=snippet.tags,
                variables=snippet.variables,
                edited_by=user.id,
            )
        )
        imported += 1

    db.add(
        AuditLog(
            workspace_id=workspace_id,
            user_id=user.id,
            action="import",
            meta={"count": imported},
        )
    )
    db.commit()
    record_snippet_mutation("import")
    return {"imported": imported}
