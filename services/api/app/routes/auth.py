"""Development auth endpoints (placeholder until OAuth)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/magic", response_model=schemas.AuthToken)
def magic_link_login(payload: schemas.MagicLinkRequest, db: Session = Depends(get_db)) -> schemas.AuthToken:
    """Issue a development token for the provided email address."""

    # TODO: swap this stub with actual magic-link creation logic and persistence
    fake_token = f"dev-token-for:{payload.email}"
    return schemas.AuthToken(access_token=fake_token)
