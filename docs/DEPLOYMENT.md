# ClassGen Deployment — class.dater.world

## Production Host

| | |
|---|---|
| **Server** | DigitalOcean droplet `dater-flow` (`165.22.80.123`) |
| **Domain** | `class.dater.world` (A record → 165.22.80.123) |
| **SSL** | Auto via nginx-proxy + letsencrypt-companion |
| **Repo path** | `/var/opt/ns.classgen` |
| **Symlink** | `/var/www/class.dater.world → /var/opt/ns.classgen` |
| **Compose file** | `deploy/docker-compose.nginx-proxy.yml` |
| **Env file** | `deploy/.env.prod` (on server only, gitignored) |

## Architecture

```
Internet (HTTPS 443)
  ↓
nginx-proxy (jwilder/nginx-proxy, shared across all sites)
  ↓  VIRTUAL_HOST=class.dater.world
classgen-app (:8000, 2 uvicorn workers)
  ├─→ OpenRouter LLM (x-ai/grok-4.1-fast)
  ├─→ PostgREST (:3000) → Postgres 16 (persistent storage)
  └─→ Redis (session cache, batch jobs)
```

The droplet runs a shared nginx-proxy + letsencrypt-companion stack on the `proxy` Docker network. Each app sets `VIRTUAL_HOST` and `LETSENCRYPT_HOST` env vars for auto-discovery.

## Containers

| Container | Image | Network | Purpose |
|---|---|---|---|
| `classgen-app` | Custom (Python 3.14, FastAPI) | `proxy` + `deploy_default` | Application server |
| `classgen-db` | `postgres:16-alpine` | `deploy_default` | Persistent database |
| `classgen-rest` | `postgrest/postgrest:v12.2.3` | `deploy_default` | REST API for DB (Supabase-compatible) |
| `classgen-redis` | `redis:7-alpine` | `deploy_default` | Cache + batch job queue |

## Deploy / Update

```bash
ssh root@165.22.80.123
cd /var/opt/ns.classgen

# Pull latest code
git pull

# Rebuild and restart (--env-file is required for DB secrets)
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.nginx-proxy.yml up -d --build

# Run any pending migrations
docker exec classgen-app /app/.venv/bin/python -m migrations.runner

# Reload PostgREST schema cache (if migrations added/removed columns)
docker restart classgen-rest

# Tail logs
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.nginx-proxy.yml logs -f app
```

## Migrations

Schema changes are managed via numbered SQL files in `migrations/`. See [DATABASE.md](DATABASE.md) for details.

```bash
# Check status
docker exec classgen-app /app/.venv/bin/python -m migrations.runner status

# Apply pending
docker exec classgen-app /app/.venv/bin/python -m migrations.runner
```

## Health Check

```bash
curl https://class.dater.world/health
# {"status":"ok"}
```

## Environment Variables

Stored in `deploy/.env.prod` on the server (not in git). See `deploy/.env.prod.example` for the full template.

**Required:**

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | LLM API key |
| `POSTGRES_PASSWORD` | Database password (generate: `openssl rand -base64 24 \| tr -d '/+='`) |
| `PGRST_JWT_SECRET` | PostgREST JWT signing secret (min 32 chars) |
| `SUPABASE_ANON_KEY` | JWT for `classgen_api` role, signed with `PGRST_JWT_SECRET` |
| `VIRTUAL_HOST` | Domain for nginx-proxy auto-discovery |
| `LETSENCRYPT_HOST` | Domain for SSL cert provisioning |

**Optional:** `TWILIO_*` (WhatsApp), `VAPID_*` (push notifications), `PAYSTACK_SECRET_KEY` (billing)

**Set automatically by compose:** `SUPABASE_URL`, `REDIS_URL`, `DATABASE_URL`, `APP_ROOT`

## Logs & Debugging

```bash
# App logs
docker logs classgen-app --tail 50 -f

# Database logs
docker logs classgen-db --tail 20

# PostgREST logs
docker logs classgen-rest --tail 20

# Redis
docker logs classgen-redis --tail 20

# nginx-proxy config (verify routing)
docker exec nginx-proxy cat /etc/nginx/conf.d/default.conf | grep -A5 'class.dater'

# Restart single service
docker restart classgen-app

# Connect to database directly
docker exec -it classgen-db psql -U postgres -d classgen
```

## Other Sites on This Host

| Domain | Path | Purpose |
|---|---|---|
| `wa.dater.world` | `/var/www/wa.dater.world` | WhatsApp service |
| `flow.dater.world` | `/var/www/flow.dater.world` | n8n automation |
| `ag.dater.world` | `/var/www/ag.dater.world` | Agent |
| `qd.dater.world` | `/var/www/qd.dater.world` | Qdrant |

## Local Staging (before production deploy)

Always run a full Docker staging locally before deploying to production. Unit tests miss Docker-specific failures (path resolution, JWT signatures, build ordering).

```bash
# Clean slate
docker compose down -v
docker compose up -d --build

# Run migrations
docker compose exec app /app/.venv/bin/python -m migrations.runner

# Staging checklist
curl http://localhost:8000/health

# DB write
curl -X POST http://localhost:8000/api/teacher/register \
  -H 'Content-Type: application/json' \
  -d '{"thread_id":"stg_t1","name":"Mrs. Staging"}'

# DB read
curl "http://localhost:8000/api/teacher/profile?thread_id=stg_t1"

# LLM + PDF + homework
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"SS2 Biology: Photosynthesis","thread_id":"stg_t1"}'
```

## History

### Initial Setup (2026-03-24)

1. Created repo `kulemantu/ns.classgen` on GitHub
2. Cloned to `/var/opt/ns.classgen`, symlinked to `/var/www/class.dater.world`
3. Created `deploy/docker-compose.nginx-proxy.yml` (no Caddy — uses shared nginx-proxy)
4. Configured `deploy/.env.prod` with OpenRouter + VAPID keys
5. Built and started: `docker compose -f deploy/docker-compose.nginx-proxy.yml up -d --build`
6. nginx-proxy auto-detected container, provisioned Let's Encrypt cert

### Database Addition (2026-04-02)

1. Added Postgres 16 + PostgREST to production compose (was in-memory only)
2. Created `classgen_api` DB role (least-privilege, replaces `postgres` superuser for PostgREST)
3. Generated strong Postgres password + JWT secret (stored in `deploy/.env.prod`)
4. Added migration tooling (`migrations/runner.py`)
5. Applied 002 migration: `updated_at` columns + auto-update triggers on mutable tables
6. Compose command now requires `--env-file deploy/.env.prod` (fail-fast on missing secrets)
