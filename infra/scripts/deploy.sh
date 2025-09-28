#!/usr/bin/env bash
set -euo pipefail

# Usage: DEPLOY_HOST=user@host ./infra/scripts/deploy.sh
# Requires passwordless SSH access with Docker installed on the remote host.

if [ -z "${DEPLOY_HOST:-}" ]; then
  echo "DEPLOY_HOST not set" >&2
  exit 1
fi

REMOTE_COMPOSE_DIR=${REMOTE_COMPOSE_DIR:-/opt/text-expander}

ssh "$DEPLOY_HOST" <<'EOF'
  set -euo pipefail
  cd "$REMOTE_COMPOSE_DIR"
  docker compose pull
  docker compose up -d --remove-orphans
EOF
