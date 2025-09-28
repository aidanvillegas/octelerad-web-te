# Docker Infrastructure

This directory contains container definitions for local development and deployment.

## Stack
- `postgres`: Postgres 16 (data stored in the `pgdata` volume)
- `api.Dockerfile`: FastAPI backend image (runs Alembic migrations on start)
- `web.Dockerfile`: Next.js frontend image
- `docker-compose.yml`: Orchestrates Postgres, API, Web, and Caddy reverse proxy
- `env/api.env`: Environment variables consumed by the API service (`DB_URL`)
- `env/postgres.env`: Credentials for the Postgres container

## Usage

From `infra/docker` run:

```bash
docker compose up --build
```

Caddy terminates TLS locally, so browse to `https://app.localhost` for the web UI and `https://api.localhost/docs` for the API documentation.
