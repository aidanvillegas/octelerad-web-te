# Docker Infrastructure

This directory contains container definitions for local development and deployment.

## Stack
- `api.Dockerfile`: FastAPI backend image
- `web.Dockerfile`: Next.js frontend image
- `docker-compose.yml`: Orchestrates API, Web, and Caddy reverse proxy
- `env/api.env`: Environment variables consumed by the API service

## Usage

From `infra/docker` run:

```bash
docker compose up --build
```

Caddy proxies `http://app.localhost` to the web container and `http://api.localhost` to the API container.
