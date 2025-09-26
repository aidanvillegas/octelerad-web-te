"""Reusable FastAPI dependencies."""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> Dict[str, Any]:
    """Temporary stand-in for authenticated user lookup."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # TODO: replace with real JWT / OAuth validation once implemented
    return {"id": 0, "email": "placeholder@example.com", "token": credentials.credentials}
