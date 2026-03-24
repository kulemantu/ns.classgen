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
  ├─→ Redis (classgen-redis, internal)
  └─→ In-memory storage (no Supabase configured yet)
```

The droplet runs a shared nginx-proxy + letsencrypt-companion stack on the `proxy` Docker network. Each app sets `VIRTUAL_HOST` and `LETSENCRYPT_HOST` env vars for auto-discovery.

## Containers

| Container | Image | Network |
|---|---|---|
| `classgen-app` | Custom (Python 3.14, FastAPI) | `proxy` + `deploy_default` |
| `classgen-redis` | `redis:7-alpine` | `deploy_default` |

## Deploy / Update

```bash
ssh root@165.22.80.123

cd /var/opt/ns.classgen
git pull
docker compose -f deploy/docker-compose.nginx-proxy.yml up -d --build
docker compose -f deploy/docker-compose.nginx-proxy.yml logs -f app
```

## Health Check

```bash
curl https://class.dater.world/health
# {"status":"ok"}
```

## Environment Variables

Stored in `deploy/.env.prod` on the server (not in git). Template:

```
OPENROUTER_API_KEY=sk-or-v1-...
VIRTUAL_HOST=class.dater.world
LETSENCRYPT_HOST=class.dater.world
LETSENCRYPT_EMAIL=admin@dater.world
SUPABASE_URL=
SUPABASE_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
VAPID_PRIVATE_KEY=...
VAPID_PUBLIC_KEY=...
VAPID_CONTACT=mailto:admin@dater.world
PAYSTACK_SECRET_KEY=
```

## Logs & Debugging

```bash
# App logs
docker logs classgen-app --tail 50 -f

# Redis
docker logs classgen-redis --tail 20

# nginx-proxy config (verify routing)
docker exec nginx-proxy cat /etc/nginx/conf.d/default.conf | grep -A5 'class.dater'

# Restart
docker compose -f deploy/docker-compose.nginx-proxy.yml restart app
```

## Other Sites on This Host

| Domain | Path | Purpose |
|---|---|---|
| `wa.dater.world` | `/var/www/wa.dater.world` | WhatsApp service |
| `flow.dater.world` | `/var/www/flow.dater.world` | n8n automation |
| `ag.dater.world` | `/var/www/ag.dater.world` | Agent |
| `qd.dater.world` | `/var/www/qd.dater.world` | Qdrant |

## Initial Setup (2026-03-24)

1. Created repo `kulemantu/ns.classgen` on GitHub
2. Cloned to `/var/opt/ns.classgen`, symlinked to `/var/www/class.dater.world`
3. Created `deploy/docker-compose.nginx-proxy.yml` (no Caddy — uses shared nginx-proxy)
4. Configured `deploy/.env.prod` with OpenRouter + VAPID keys
5. Built and started: `docker compose -f deploy/docker-compose.nginx-proxy.yml up -d --build`
6. nginx-proxy auto-detected container, provisioned Let's Encrypt cert
7. Verified: `https://class.dater.world/health` → `{"status":"ok"}`
