"""FastAPI application factory and ASGI entrypoint."""

from fastapi import FastAPI

from .config import settings
from .database import engine
from . import models
from .routes import auth, health, snippets

models.Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="Macro Library API", version="0.1.0", docs_url="/docs")

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(snippets.router)

    @app.get("/", tags=["meta"])
    def index():
        return {"service": "macro-library-api", "environment": settings.environment}

    return app


app = create_app()
