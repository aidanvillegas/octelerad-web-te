# Copilot Instructions for Macro Library

## Architecture Overview

This is a full-stack **Macro Library** web application for managing text expansion snippets. The system is built as a monorepo with clear service boundaries:

- **Frontend**: Next.js App Router (`apps/web/`) - Single-page client for snippet CRUD, search, and workspace management
- **Backend**: FastAPI (`services/api/`) - REST API with SQLAlchemy, JWT auth, and Prometheus metrics  
- **Infrastructure**: Docker Compose stack (`infra/docker/`) with Caddy reverse proxy for local TLS

## Key Architectural Patterns

### Multi-tenant Workspace Model
- Every snippet belongs to a `Workspace` via `workspace_id` foreign key
- User access controlled through `Membership` table (users can belong to multiple workspaces)
- All API endpoints are scoped: `/workspaces/{workspace_id}/snippets`
- Use `require_membership()` utility in route handlers to enforce access

### Snippet Versioning & Audit Trail
- Each snippet change creates new `SnippetVersion` record (never update existing)
- All mutations logged to `AuditLog` via `record_snippet_mutation()` helper
- Restore functionality by copying version data back to main `Snippet` record
- API returns current version number in responses for conflict detection

### Authentication Flow
- **Dev**: Magic link auth (`/auth/magic`) returns JWT in `access_token` field
- **Frontend**: Stores JWT in component state, includes in `Authorization: Bearer {token}` headers
- **Backend**: JWT validation via `get_current_user()` dependency injection

## Development Workflows

### Local Development Setup
```bash
# Backend (requires Python venv)
python -m venv .venv && . .venv/Scripts/Activate.ps1
pip install -r services/api/requirements.txt
uvicorn services.api.app.main:app --reload  # or `make api-dev`

# Frontend (separate terminal)
cd apps/web && npm install && npm run dev  # or `make web-dev`

# Full stack with TLS
cd infra/docker && docker compose up --build  # or `make docker-up`
# Access: https://app.localhost (web), https://api.localhost/docs (API docs)
```

### Database Migrations
- Use Alembic for schema changes: `cd services/api && alembic revision --autogenerate -m "description"`
- Apply locally: `make migrate` or `cd services/api && alembic upgrade head`
- Models in `services/api/app/models.py` auto-generate SQLAlchemy tables

### Testing Patterns
- **Backend**: pytest with TestClient in `services/api/tests/` - use `authenticate()` helper for JWT setup
- **Frontend**: Playwright E2E in `apps/web/tests/e2e/` - mock API routes for isolated testing
- Run tests: `make test-api` and `make test-web`

#### Pytest on Windows (monorepo imports)
- Run pytest from the repo root so absolute imports like `from services.api.app ...` work:
	- PowerShell: `Set-Location <repo-root>; pytest services/api/tests -q`
- Ensure packages exist: add `services/__init__.py`, `services/api/__init__.py`, and `services/api/app/__init__.py`.
- If needed, set `PYTHONPATH` for the session:
	- PowerShell: `$Env:PYTHONPATH = "$PWD"; pytest services/api/tests -q`

## Project-Specific Conventions

### API Response Patterns
- List endpoints return arrays directly (not wrapped in `{data: []}`)
- Error responses use FastAPI's HTTPException with appropriate status codes
- All mutation endpoints record audit trail via `record_snippet_mutation()` before response

### Frontend State Management
- Single-component state with React hooks (no external state management)
- API calls wrapped in try/catch with user-facing error/success messages
- Uses `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8000`)

### Environment Configuration  
- **Backend**: Pydantic Settings in `config.py` with `.env` file support
- **Frontend**: Next.js environment variables (prefix with `NEXT_PUBLIC_` for client-side)
- **Docker**: Environment files in `infra/docker/env/api.env`

### Import/Export Format
- JSON schema `text-expander.v1` for snippet export/import
- Includes full snippet metadata (tags array, variables object, timestamps)
- Delta sync endpoint compares `updated_at` timestamps for incremental updates

## Integration Points

### Cross-service Communication
- Frontend ↔ Backend: REST API over HTTP with JWT authentication
- Local development: Direct HTTP calls to `localhost:8000`
- Production: Caddy reverse proxy terminates TLS and routes by subdomain

### External Dependencies
- **Database**: SQLite for local dev, PostgreSQL for production (via `DB_URL` env var)
- **Observability**: Prometheus metrics at `/metrics`, health check at `/healthz`
- **TLS**: Caddy auto-generates certificates for `*.localhost` domains