# Deployment Runbook

1. Ensure Docker is installed on the target host and the compose bundle from `infra/docker` is copied to `/opt/text-expander` (or your chosen path).
2. Authenticate to GitHub Container Registry so the host can pull `ghcr.io/<repo>/api` and `ghcr.io/<repo>/web` images.
3. From your workstation, build and push via CI (merge to `main`).
4. Deploy with SSH:

```bash
DEPLOY_HOST=user@host REMOTE_COMPOSE_DIR=/opt/text-expander ./infra/scripts/deploy.sh
```

The script runs `docker compose pull` followed by `docker compose up -d --remove-orphans`, ensuring the latest images are running with zero downtime.
