"""Placeholder snippet endpoints for the MVP build-out."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/workspaces/{workspace_id:int}/snippets", tags=["snippets"])


@router.get("", response_model=List[schemas.SnippetOut])
def list_snippets(workspace_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> List[schemas.SnippetOut]:
    """Return an empty list until persistence is wired up."""

    # TODO: replace stub with real query using models.Snippet once implemented
    return []


@router.post("", response_model=schemas.SnippetOut, status_code=status.HTTP_201_CREATED)
def create_snippet(
    workspace_id: int,
    payload: schemas.SnippetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Stubbed snippet creation endpoint."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Snippet creation not implemented yet")


@router.put("/{snippet_id:int}", response_model=schemas.SnippetOut)
def update_snippet(
    workspace_id: int,
    snippet_id: int,
    payload: schemas.SnippetUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Stubbed snippet update endpoint."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Snippet update not implemented yet")


@router.post("/{snippet_id:int}/restore/{version:int}", response_model=schemas.SnippetOut)
def restore_snippet_version(
    workspace_id: int,
    snippet_id: int,
    version: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> schemas.SnippetOut:
    """Stubbed snippet version restore endpoint."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Version restore not implemented yet")


@router.get("/since", response_model=List[schemas.SnippetDelta])
def snippets_since(
    workspace_id: int,
    since_ts: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> List[schemas.SnippetDelta]:
    """Stubbed delta sync endpoint."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Delta sync not implemented yet")
