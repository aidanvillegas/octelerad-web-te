"""Health and readiness endpoints."""

from fastapi import APIRouter

from .. import schemas

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=schemas.HealthStatus)
def healthcheck() -> schemas.HealthStatus:
    """Simple health endpoint for probes."""

    return schemas.HealthStatus(status="ok")
