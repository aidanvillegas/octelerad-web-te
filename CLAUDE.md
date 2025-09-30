# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack **public datasets collaboration platform** built as a monorepo. The system enables anonymous users to create, edit, and collaborate on datasets in realtime with WebSocket synchronization.

**Stack:**
- **Frontend**: Next.js 14 App Router with AG Grid for spreadsheet-style editing
- **Backend**: FastAPI with SQLAlchemy, WebSocket support, and Prometheus metrics
- **Database**: PostgreSQL (production), SQLite (local dev)
- **Infrastructure**: Docker Compose with Caddy reverse proxy

## Essential Commands

### Development

Run from repository root:

```bash
# Backend (requires Python venv)
make api-dev
# or: uvicorn services.api.app.main:app --reload

# Frontend (separate terminal)
make web-dev
# or: cd apps/web && npm run dev

# Full stack with Docker (includes Postgres + Caddy TLS)
make docker-up
# or: cd infra/docker && docker compose up --build
# Access at: https://app.localhost (web), https://api.localhost/docs (API docs)

make docker-down
# or: cd infra/docker && docker compose down
```

### Testing

**IMPORTANT on Windows (monorepo imports):**
- Always run pytest from repository root so absolute imports like `from services.api.app ...` work
- PowerShell: `Set-Location <repo-root>; pytest services/api/tests -q`
- If needed: `$Env:PYTHONPATH = "$PWD"; pytest services/api/tests -q`
- Ensure `__init__.py` exists in: `services/`, `services/api/`, and `services/api/app/`

```bash
# Backend tests
make test-api
# or: pytest services/api/tests

# Frontend tests (requires Playwright browsers: npx playwright install)
cd apps/web && npm test
# or: make test-web

# Headed mode for debugging
cd apps/web && npm run test:headed
```

### Database Migrations

```bash
# Create new migration
cd services/api && alembic revision --autogenerate -m "description"

# Apply migrations
make migrate
# or: cd services/api && alembic upgrade head
```

### Linting & Formatting

```bash
make lint          # Next.js ESLint
make format        # Auto-fix lint issues
```

## Architecture

### Realtime Collaboration Model

The system uses a **REST + WebSocket hybrid** for realtime updates:

1. **Mutations via REST**: All edits (cell updates, row inserts, deletes) go through REST endpoints in [services/api/app/routes_datasets.py](services/api/app/routes_datasets.py)
2. **Broadcasts via WebSocket**: Each REST endpoint uses `BackgroundTasks` to call `hub.broadcast()` after committing changes
3. **WebSocket listeners**: Frontend connects to `/ws/datasets/{dataset_id}` and receives JSON messages (type: `cell`, `rows_upsert`, `column_add`, `delete_rows`)
4. **Optimistic UI updates**: Frontend immediately updates local state, then syncs with server response

Key files:
- [services/api/app/realtime.py](services/api/app/realtime.py) - In-memory `DatasetHub` managing WebSocket rooms
- [services/api/app/ws.py](services/api/app/ws.py) - WebSocket route handler
- [apps/web/hooks/useWs.ts](apps/web/hooks/useWs.ts) - Frontend WebSocket hook with auto-reconnect

### Anonymous Access Model

- **No authentication required**: All dataset endpoints are open-access
- **Browser-scoped identity**: Frontend generates a `clientId` (localStorage) to tag datasets created on that device
- **"Created on this browser" filtering**: `/datasets/mine-local?client_id={id}` returns datasets created by that client
- **Public dataset list**: `/datasets/all` shows all datasets ordered by `updated_at`

### Database Schema

**Dataset models** ([services/api/app/models_datasets.py](services/api/app/models_datasets.py)):
- `Dataset`: Top-level entity with `name`, `schema` (JSON column definitions), `created_by_client`, `owner_id` (nullable)
- `DatasetRow`: Individual rows with `dataset_id` FK, `data` (JSON), `archived` flag
- `DatasetPermission`: (future) User-based sharing control

**Audit trail** ([services/api/app/models.py](services/api/app/models.py)):
- All dataset creation logged to `AuditLog` table with `action='create_dataset'`

### Import/Export

- **Supported formats**: CSV and JSON
- **Import endpoint**: `POST /datasets/{dataset_id}/import` with file upload
  - Auto-detects columns from file headers/keys
  - Updates dataset schema to match imported structure
  - Max size: 5MB (configurable via `MAX_IMPORT_BYTES` env var)
- **Export endpoint**: `GET /datasets/{dataset_id}/export?fmt={json|csv}`
  - Returns `{filename, content}` payload for client-side download

### Frontend State Management

- **Single-component state** with React hooks (no Redux/Zustand)
- **AG Grid integration**: Editable cells with `onCellValueChanged` callback triggers REST PATCH
- **WebSocket sync**: Incoming messages update local `rows` state via `setRows()`, AG Grid auto-re-renders
- **API client**: Centralized axios instance in [apps/web/lib/api.ts](apps/web/lib/api.ts) with `NEXT_PUBLIC_API_URL` config

## Project-Specific Patterns

### Backend Conventions

- **REST response format**: Return objects/arrays directly (not wrapped in `{data: [...]}`)
- **Status codes**: Use 201 for creation, 404 for not found, 413 for too large, 400 for validation errors
- **Dependency injection**: Use `db: Session = Depends(get_db)` for database sessions
- **Background tasks**: Use `background: BackgroundTasks` parameter and `background.add_task(hub.broadcast, ...)` for async WebSocket broadcasts

### Frontend Conventions

- **API calls**: Wrap in try/catch, use `react-hot-toast` for user feedback
- **File references**: Use markdown links `[filename.ts](path/to/file.ts)` for clickable navigation
- **Environment variables**: Prefix with `NEXT_PUBLIC_` for client-side access

### Database Patterns

- **SQLite auto-create**: Tables auto-generate on startup if using SQLite (see [models_datasets.py:50-51](services/api/app/models_datasets.py))
- **Alembic for Postgres**: Use migrations for production schema changes
- **JSON columns**: Store flexible data structures (dataset `schema`, row `data`) as JSON type

## Development Workflow

1. **Local iteration**: Use `make api-dev` + `make web-dev` for fast reload cycles
2. **Integration testing**: Use `make docker-up` to test full stack with Postgres + Caddy
3. **Pre-commit checks**:
   - Run `pytest services/api/tests` from repo root (Windows: see testing section above)
   - Run `cd apps/web && npm run build` to catch TypeScript errors
   - Run `cd apps/web && npm test` for Playwright E2E validation
4. **Docker validation**: Final smoke test with `cd infra/docker && docker compose up --build`

## Common Gotchas

- **pytest import errors on Windows**: Run from repo root, not `services/api/` directory
- **WebSocket reconnection**: Frontend hook auto-reconnects on disconnect, but test timeouts may occur if API is down
- **AG Grid row IDs**: Always provide `getRowId={(params) => String(params.data.id)}` to prevent duplicate row rendering
- **CORS in local dev**: API allows all origins via `allow_origins=['*']` in [main.py:14-18](services/api/app/main.py)
