# ClassGen Deployment

Production deployment for a VPS with Docker Compose + Caddy (auto-HTTPS).

## Architecture

```
Internet
  │
  ├── HTTPS (443) ──► Caddy (auto-SSL via Let's Encrypt)
  │                      │
  │                      ▼
  │                   FastAPI app (:8000)
  │                      │
  │                      ├──► Supabase Cloud (Postgres)
  │                      └──► Redis (:6379, internal)
  │
  └── WhatsApp ──► Twilio ──► POST /webhook/twilio
```

## Prerequisites

- VPS with 2GB+ RAM (Hetzner CX22 or DigitalOcean $6/mo droplet)
- Docker + Docker Compose installed
- Domain with DNS A record pointing to the VPS IP
- Supabase Cloud project (free tier: https://supabase.com)
- Twilio account with WhatsApp sandbox or number
- OpenRouter API key

## First-time Setup

### 1. Server prep

```bash
# SSH into your VPS
ssh root@your-server-ip

# Install Docker (if not already)
curl -fsSL https://get.docker.com | sh

# Clone the repo
git clone https://github.com/your-org/classgen.git
cd classgen/deploy
```

### 2. Configure environment

```bash
cp .env.prod.example .env.prod
nano .env.prod   # Fill in all required values
```

Required values:
- `DOMAIN` — your domain (e.g., `classgen.ng`)
- `OPENROUTER_API_KEY` — from https://openrouter.ai/keys
- `SUPABASE_URL` — from your Supabase project settings
- `SUPABASE_KEY` — the `anon` key from Supabase
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` — generate with the command in the example file

### 3. Set up Supabase

Run the schema migration on your Supabase project:
- Go to Supabase Dashboard → SQL Editor
- Paste the contents of `init.sql` from the repo root
- Run it

### 4. Deploy

```bash
python deploy.py setup
```

This builds the app, starts Caddy + Redis, and verifies health.

### 5. Configure Twilio webhook

In Twilio Console → WhatsApp Sandbox (or your number):
- Set webhook URL to: `https://your-domain.com/webhook/twilio`
- Method: POST

## Updating

```bash
cd classgen/deploy
python deploy.py update
```

This pulls the latest code, rebuilds, and restarts with zero-downtime.

## Operations

```bash
# View logs (all services)
python deploy.py logs

# View logs (specific service)
python deploy.py logs app
python deploy.py logs caddy

# Check health
python deploy.py status

# Stop everything
python deploy.py stop
```

## SSL

Caddy handles SSL automatically via Let's Encrypt. No manual cert management needed. Certs are stored in a Docker volume (`caddy_data`) and auto-renewed.

Requirements:
- Port 80 and 443 must be open
- DNS A record must point to the server IP
- The domain must be set in `.env.prod`

## Backups

- **Postgres**: Supabase Cloud handles automated backups
- **Redis**: AOF persistence to Docker volume (survives restarts, not critical data)
- **PDFs**: generated on-demand, cleaned up after 24 hours (not backed up)

## Monitoring

- `GET /health` returns `{"status": "ok"}`
- Docker healthcheck on the app container (every 30s)
- Set up uptime monitoring (e.g., UptimeRobot free tier) pointing at `https://your-domain.com/health`
