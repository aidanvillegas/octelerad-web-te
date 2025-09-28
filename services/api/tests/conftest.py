"""Shared pytest fixtures for the API service."""

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.api.app import models
from services.api.app.database import get_db
from services.api.app.main import app

TEST_DB_PATH = Path(__file__).parent / "test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def override_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_URL", SQLALCHEMY_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET", "test-secret")


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    models.Base.metadata.create_all(bind=engine)
    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)
        engine.dispose()
        TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        client.close()
