# API Service

FastAPI backend for the macro library. Implements workspace memberships, snippet CRUD with version history, observability, and import/export endpoints.

## Local setup

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1  # or source .venv/bin/activate on mac/linux
pip install -r services/api/requirements.txt
uvicorn services.api.app.main:app --reload
```

Set `DB_URL` to point at Postgres when running against the container stack, e.g.:

```bash
setx DB_URL "postgresql+psycopg://macro:macro-pass@localhost:5432/text_expander"
```

## Tests

```bash
pytest services/api/tests
```

## Migrations

Alembic is preconfigured. Apply migrations locally with:

```bash
cd services/api
alembic upgrade head
```

Generate new revisions with `alembic revision -m "message" --autogenerate` after updating models.

### Features (Sprint 1)
- Dev magic-link auth issuing JWTs
- Workspace membership enforcement (auto-creates default workspace)
- Snippet CRUD with versioning
- Restore, export, import, and delta-sync endpoints
- Audit log endpoint (`/workspaces/{id}/audit`)
- Health probe at `/healthz` and Prometheus metrics at `/metrics`
- Request/Mutation metrics exposed via Prometheus client
