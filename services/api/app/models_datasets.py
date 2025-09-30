"""Dataset models for public collaborative datasets."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func, Index
from sqlalchemy.orm import relationship

from .models import Base
from .database import engine
from .config import settings


class Dataset(Base):
    __tablename__ = 'datasets'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    created_by_client = Column(String, nullable=True, index=True)
    schema = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship('User', lazy='joined')


class DatasetPermission(Base):
    __tablename__ = 'dataset_permissions'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    role = Column(String, default='viewer', nullable=False)

    __table_args__ = (Index('ix_dataset_perm_unique', 'dataset_id', 'user_id', unique=True),)


class DatasetRow(Base):
    __tablename__ = 'dataset_rows'

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# Auto-create tables for SQLite dev convenience
if settings.db_url.startswith('sqlite'):
    Base.metadata.create_all(bind=engine)
