"""Health and readiness endpoints."""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .. import schemas

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=schemas.HealthStatus)
def healthcheck() -> schemas.HealthStatus:
    """Simple health endpoint for probes."""

    return schemas.HealthStatus(status="ok")


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics for scraping."""

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
