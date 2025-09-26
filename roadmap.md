# Web Macro Library Roadmap

## 0. MVP Feature Set (Web-only)
- Workspaces & users (Org -> Members)
- Snippets (name, trigger, body, tags, variables)
- Version history & restore
- Powerful search (name/trigger/body/tags)
- Import/Export (JSON), bulk ops
- Audit log (who did what/when)
- API for existing desktop app to sync (pull-only)
- Auth (dev: magic link token; prod: OAuth), RBAC (Admin, Editor, Viewer)
- Observability (health, metrics) & CI/CD

**Non-goals**
- System-wide expansion
- Browser extensions
- Native helpers (desktop app covers this)

## 1. Repository Layout (Monorepo)
```
text-expander/
+- apps/
¦  +- web/                     # Next.js (App Router, TS)
+- services/
¦  +- api/                     # FastAPI backend
+- infra/
¦  +- docker/                  # Dockerfiles & docker-compose
¦  +- caddy/                   # Caddy reverse proxy + TLS
+- docs/
¦  +- SOPs/                    # Standard Operating Procedures
¦  +- ADRs/                    # Architecture Decision Records
+- .github/workflows/          # CI/CD
+- Makefile
```

## 2. Backend API (FastAPI)
- `services/api/app/models.py`: SQLAlchemy models for workspaces, users, memberships, snippets, versions, audit logs, API keys
- `services/api/app/auth.py`: Dev magic-link auth (placeholder for OAuth) and token verification
- `services/api/app/main.py`: Snippet CRUD with versioning, restore, import/export, delta sync, health endpoint
- Enforces unique triggers per workspace and records audit history

## 3. Export/Import JSON Schema
- Stable schema `text-expander.v1`
- Includes snippets with metadata (tags, variables, updated_at)
- Safe for git storage and environment portability

## 4. Frontend (Next.js MVP)
- `apps/web/app/page.tsx`: Auth via dev magic link, search, CRUD, export link
- Uses `NEXT_PUBLIC_API_URL`
- Provides snippet creation form with tags/variables handling

## 5. Containerization & Deploy
- API Dockerfile (`infra/docker/api.Dockerfile`)
- Web Dockerfile (`infra/docker/web.Dockerfile`)
- Caddy reverse proxy (`infra/caddy/Caddyfile`)
- Docker Compose stack (`infra/docker/docker-compose.yml`)
- Environment file (`infra/docker/env/api.env`)
- DNS -> Host, `docker compose up -d --build`

## 6. CI/CD (GitHub Actions -> GHCR -> SSH deploy)
- Build & push API/Web images
- SSH to host, update compose stack, restart services
- Provides immutable releases and rollback path

## 7. Post-MVP Hardening
- Postgres + Alembic migrations and backups
- Full-text search (tsvector + GIN)
- RBAC UI and invite flow
- API keys (hashed) for desktop sync without user tokens
- Variable placeholder validation
- Bulk operations with dry run and conflict reporting
- Audit log UI + export
- Observability: OTEL traces, /metrics, structured logs

## 8. Testing
- API: pytest + FastAPI TestClient (CRUD, versioning, import/export, delta sync)
- Web: Playwright smoke tests (login, create, search, export)
- Security: OWASP ZAP baseline scan in CI

## 9. Compliance, Reliability, UX
- Compliance: No sensitive data in logs, immutable audit logs, key rotation
- Reliability: Health checks, rate limiting, graceful shutdown, DB pooling
- UX: WCAG accessibility, keyboard-first interactions, diff view for restores, dark mode support
## 10. Two-Sprint Backlog
**Sprint 1 (MVP)**
- [x] Scaffold monorepo directories (apps/web, services/api, infra, docs, workflows)
- [ ] Provide Dockerfiles and docker-compose baseline
- [ ] Implement models & endpoints (CRUD, restore, export, import, delta sync)
- [ ] Next.js list/search/create UI
- [ ] CI/CD pipeline to GHCR + SSH deploy
- [ ] Health checks + basic audit log

**Sprint 2 (Hardening)**
- [ ] Switch to Postgres + Alembic; add FTS (tsvector + GIN)
- [ ] RBAC UI + invite flow
- [ ] API keys (read-only) for desktop sync
- [ ] Import dry run + conflict report
- [ ] Audit log UI + CSV export
- [ ] Metrics dashboard (p95 latency, error rate, import counts, top searches)

