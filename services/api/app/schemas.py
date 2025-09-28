"""Pydantic schemas for request/response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MagicLinkRequest(BaseModel):
    email: str = Field(..., description="User email to send the magic link to")


class SnippetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    trigger: str = Field(..., min_length=1, max_length=64)
    body: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    variables: Dict[str, str] = Field(default_factory=dict)


class SnippetCreate(SnippetBase):
    """Schema for creating a snippet."""


class SnippetUpdate(SnippetBase):
    """Schema for updating a snippet."""


class SnippetOut(SnippetBase):
    id: int
    version: int = 1
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthStatus(BaseModel):
    status: str


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Message(BaseModel):
    detail: str


class DeltaQuery(BaseModel):
    since_ts: str


class SnippetDelta(SnippetOut):
    """Snippet payload for delta sync responses."""


class AuditLogOut(BaseModel):
    id: int
    workspace_id: int
    user_id: Optional[int]
    action: str
    meta: Dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True
