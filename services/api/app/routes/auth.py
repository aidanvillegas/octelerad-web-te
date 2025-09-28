"""Development auth endpoints (placeholder until OAuth)."""

from fastapi import APIRouter, Depends
from jose import jwt
from sqlalchemy.orm import Session

from .. import schemas
from ..config import settings
from ..database import get_db
from ..models import Membership, User, Workspace

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_or_create_workspace(db: Session) -> Workspace:
    workspace = db.query(Workspace).order_by(Workspace.id).first()
    if workspace is None:
        workspace = Workspace(name="Default Workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    return workspace


@router.post("/magic", response_model=schemas.AuthToken)
def magic_link_login(payload: schemas.MagicLinkRequest, db: Session = Depends(get_db)) -> schemas.AuthToken:
    """Issue a development JWT for the provided email address."""

    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    workspace = _get_or_create_workspace(db)
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id, Membership.workspace_id == workspace.id)
        .first()
    )
    if membership is None:
        membership = Membership(user_id=user.id, workspace_id=workspace.id, role="admin")
        db.add(membership)
        db.commit()

    token = jwt.encode({"sub": str(user.id)}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return schemas.AuthToken(access_token=token)
