# Migration & Startup Instructions (Local ? Linux NAS)

This guide deploys the Text Expander stack from your local machine to a Linux NAS reachable at `drsarai-@192.168.4.150`, serving the app at `textexpander.octelerad.pserv` with Caddy TLS. It covers prerequisites, one-time host setup, deployment, and validation.

---

## 0) Prerequisites

- Local (Windows):
  - Docker Desktop installed and running.
  - Git + a shell (PowerShell).
  - Access to your GitHub repository (for CI images) or the source tree (to build images).
- NAS (Linux) at `192.168.4.150`:
  - Docker Engine + docker compose plugin installed.
  - A user with SSH access (provided: `drsarai-`).
  - Ports 80/443 open to the internet if you want Caddy to auto-provision TLS via ACME.
- DNS:
  - Create the following A/AAAA records pointing to the NAS public IP:
    - `textexpander.octelerad.pserv` ? Web UI
    - `api.textexpander.octelerad.pserv` ? API

> Note: You can also run without public DNS/TLS by changing the Caddyfile to use `:80` and skipping certs; below assumes public TLS.

---

## 1) One-time setup on the NAS

SSH into the NAS and prepare a deployment directory:

```bash
ssh drsarai-@192.168.4.150
sudo mkdir -p /opt/text-expander
sudo chown "$USER":"$USER" /opt/text-expander
exit
```

From your local machine, copy the docker bundle (compose + caddy + env files) to the NAS:

```powershell
# From repo root
scp -r infra/docker drsarai-@192.168.4.150:/opt/text-expander/
scp -r infra/caddy drsarai-@192.168.4.150:/opt/text-expander/
```

Create/adjust environment files on the NAS:

```bash
ssh drsarai-@192.168.4.150 <<'EOF'
set -e
cd /opt/text-expander
# API env (uses Postgres container from compose)
cat > infra/docker/env/api.env <<EOT
DB_URL=postgresql+psycopg://macro:macro-pass@postgres:5432/text_expander
JWT_SECRET=change-me
EOT

# Postgres credentials
cat > infra/docker/env/postgres.env <<EOT
POSTGRES_DB=text_expander
POSTGRES_USER=macro
POSTGRES_PASSWORD=macro-pass
EOT
EOF
```

Update the Caddyfile on the NAS to use your domains:

```bash
ssh drsarai-@192.168.4.150 <<'EOF'
set -e
cd /opt/text-expander
cat > infra/caddy/Caddyfile <<'CADDY'
textexpander.octelerad.pserv {
  reverse_proxy web:3000
}
api.textexpander.octelerad.pserv {
  reverse_proxy api:8000
}
CADDY
EOF
```

Point the frontend at the public API URL by editing the compose file’s `web` service on the NAS:

```bash
ssh drsarai-@192.168.4.150 "sed -i 's#NEXT_PUBLIC_API_URL=.*#NEXT_PUBLIC_API_URL=https://api.textexpander.octelerad.pserv#' /opt/text-expander/infra/docker/docker-compose.yml"
```

---

## 2) Choose your image source

There are two ways to provide images for the NAS to run.

### Option A: Pull from GitHub Container Registry (recommended)

- Ensure your CI is building and pushing `api` and `web` images to GHCR.
- On the NAS, authenticate to GHCR:

```bash
ssh drsarai-@192.168.4.150
echo "<YOUR_GHCR_PAT>" | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
exit
```

- Update `/opt/text-expander/infra/docker/docker-compose.yml` on the NAS to use `image:` entries instead of `build:` for `api` and `web`, e.g.:

```yaml
  api:
    image: ghcr.io/<org>/<repo>/api:<tag>
    env_file: [./env/api.env]
    depends_on:
      postgres:
        condition: service_healthy
    ports: ["8000:8000"]
    networks: [app]

  web:
    image: ghcr.io/<org>/<repo>/web:<tag>
    environment:
      - NEXT_PUBLIC_API_URL=https://api.textexpander.octelerad.pserv
    ports: ["3000:3000"]
    depends_on: [api]
    networks: [app]
```

> Replace `<org>/<repo>` and `<tag>` with the values from your latest GitHub Actions run (e.g., the commit SHA tag).

### Option B: Build on the NAS (no registry)

If you prefer building on the NAS, keep the compose `build:` entries. Nothing else is needed beyond copying the repo’s `infra/docker` and `infra/caddy` folders as you did above.

---

## 3) Start the stack

```bash
ssh drsarai-@192.168.4.150 <<'EOF'
set -e
cd /opt/text-expander/infra/docker
# Recreate with latest configs
docker compose down
docker compose up -d --build
# Optional: follow logs for a minute
docker compose logs -f --tail=200
EOF
```

You should see Postgres become `healthy`, the API run Alembic migrations once, then `web` and `caddy` report started.

---

## 4) Validate

- Open https://textexpander.octelerad.pserv ? you should see the UI.
- Open https://api.textexpander.octelerad.pserv/healthz ? `{ "status": "ok" }`.
- Open https://api.textexpander.octelerad.pserv/metrics ? Prometheus metrics text.
- In the UI, click “Dev Login”, create a snippet, and check the audit log renders.

If something breaks, fetch logs on the NAS:

```bash
essh drsarai-@192.168.4.150 "cd /opt/text-expander/infra/docker && docker compose ps && docker compose logs --tail=200"
```

---

## 5) Ongoing updates (fast path)

From your local workstation (after pushing images or updating the compose bundle), run:

```powershell
$env:DEPLOY_HOST = "drsarai-@192.168.4.150"
$env:REMOTE_COMPOSE_DIR = "/opt/text-expander"
./infra/scripts/deploy.sh
```

This SSHes into the NAS, does a `docker compose pull` (if using GHCR images) and `docker compose up -d --remove-orphans`.

---

## 6) Notes & rollback

- First run performs DB migrations automatically (API container runs Alembic).
- To reset the Postgres volume (data loss!):

```bash
ssh drsarai-@192.168.4.150 "cd /opt/text-expander/infra/docker && docker compose down -v && docker compose up -d"
```

- To switch environments, edit `infra/docker/env/api.env` and `infra/docker/env/postgres.env` on the NAS, then `docker compose up -d`.

- If using GHCR images, keep your PAT in a secret store on the NAS (not in shell history). Consider creating a read-only deploy token.

---

## 7) Quick reference

- Start: `ssh drsarai-@192.168.4.150 && cd /opt/text-expander/infra/docker && docker compose up -d`
- Stop: `ssh drsarai-@192.168.4.150 && cd /opt/text-expander/infra/docker && docker compose down`
- Logs: `ssh drsarai-@192.168.4.150 "cd /opt/text-expander/infra/docker && docker compose logs -f --tail=200"`
- Health: `curl -k https://api.textexpander.octelerad.pserv/healthz`
- UI: `https://textexpander.octelerad.pserv`
