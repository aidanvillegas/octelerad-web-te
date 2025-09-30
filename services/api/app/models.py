"""SQLAlchemy models for the Macro Library API."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    members = relationship("Membership", back_populates="workspace", cascade="all, delete-orphan")
    snippets = relationship("Snippet", back_populates="workspace", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    role = Column(String, default="viewer", nullable=False)  # admin|editor|viewer

    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="members")

    __table_args__ = (UniqueConstraint("user_id", "workspace_id", name="uq_memberships_user_workspace"),)


class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    trigger = Column(String, index=True, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    variables = Column(JSON, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    workspace = relationship("Workspace", back_populates="snippets")
    versions = relationship("SnippetVersion", back_populates="snippet", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("workspace_id", "trigger", name="uq_snippets_workspace_trigger"),
    )


class SnippetVersion(Base):
    __tablename__ = "snippet_versions"

    id = Column(Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey("snippets.id"), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    variables = Column(JSON, nullable=True)
    edited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    snippet = relationship("Snippet", back_populates="versions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


from .database import engine

# Ensure dataset models are imported so metadata includes them
from .models_datasets import Dataset, DatasetRow, DatasetPermission  # noqa: F401

Base.metadata.create_all(bind=engine)
