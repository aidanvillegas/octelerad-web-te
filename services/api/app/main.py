"""FastAPI application factory and ASGI entrypoint."""

import time
from fastapi import FastAPI, Request

from .config import settings
from .database import engine
from . import models
from .metrics import REQUEST_COUNT, REQUEST_LATENCY
from .routes import audit, auth, health, snippets


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="Macro Library API", version="0.2.0", docs_url="/docs")

    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        duration = time.perf_counter() - start
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)
        REQUEST_COUNT.labels(method=request.method, path=path, status=response.status_code).inc()
        return response

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(snippets.router)
    app.include_router(audit.router)

    @app.get("/", tags=["meta"])
    def index():
        return {"service": "macro-library-api", "environment": settings.environment}

    return app


app = create_app()
