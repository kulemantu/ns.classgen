# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

ClassGen is an AI lesson activity generator for African secondary school teachers. Teachers send a topic via WhatsApp or a web chat UI and receive a structured 5-block lesson pack (Opener, Explain, Activity, Homework, Teacher Notes). The app also generates homework quiz codes, tracks student submissions, manages teacher profiles/schools, and handles billing.

## Commands

```bash
# Install dependencies
uv sync

# Run the server (local dev — no external services required)
uv run python main.py
# Serves on http://localhost:8000

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_main.py -v

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run pyright

# Docker local dev (app + Postgres + PostgREST + Redis)
docker compose up -d --build
docker compose exec app /app/.venv/bin/python -m migrations.runner

# Migrations (requires DATABASE_URL or running Postgres)
docker compose exec app /app/.venv/bin/python -m migrations.runner          # apply pending
docker compose exec app /app/.venv/bin/python -m migrations.runner status   # show applied/pending
```

## Architecture (V4.0)

Package layout under `src/classgen/` with layered dependencies: `core` ← `data` ← `services` ← `api`, `channels` ← `core`.

```
src/classgen/
  api/             FastAPI routers: app.py, chat.py, webhook.py, homework.py, teacher.py, profile.py, school.py, push.py, dev.py, schemas.py
  channels/        Rendering adapters (web, WhatsApp, PDF, SMS) — placeholder for V4.1
  commands/        WhatsApp command router (router.py) + 16 handlers (handlers.py)
  content/         Prompts, curriculum data, PDF generator, worksheet generator
  core/            Domain models (billing tiers, UsageCheck) — no I/O
  data/            Persistence layer: 11 modules (sessions, teachers, homework, quiz, lessons, subscriptions, schools, parents, push, threads, client)
  integrations/    Third-party clients: Twilio, Redis queue
  services/        Business logic: LLM client, billing, notifications
  i18n.py          Locale/currency formatting
```

Root `main.py` exposes `app` via `from classgen.api.app import app`, and includes an `if __name__ == "__main__"` dev runner block that starts uvicorn with reload enabled when you run `python main.py`. Dockerfile CMD unchanged: `uvicorn main:app`.

### Channels (adapter pattern)

Two delivery channels share the same lesson generation core and command router:

- **Web chat** (`POST /api/chat`) — browser-based UI in `index.html`. Renders lesson blocks as rich cards.
- **WhatsApp** (`POST /webhook/twilio`) — Twilio webhook, returns TwiML. Same command routing, plain-text rendering.

V4.1 will formalize this into `src/classgen/channels/` with explicit rendering adapters per channel. Design spec in `docs/DESIGN-v4-structured-output.md`.

### Database

- **Postgres 16 + PostgREST v12** in both dev (Docker Compose) and production.
- **In-memory fallback** — when `SUPABASE_URL`/`SUPABASE_KEY` are unset, data modules use plain dicts. No DB needed to run locally without Docker.
- **supabase-py client** patches the internal `_postgrest` client for raw PostgREST compatibility (supabase-py appends `/rest/v1/` which raw PostgREST doesn't serve).
- **classgen_api** DB role — least-privilege (SELECT/INSERT/UPDATE/DELETE only). JWT must match `PGRST_JWT_SECRET`.
- Migrations in `migrations/` use psycopg directly against `DATABASE_URL` (not PostgREST).
- `APP_ROOT=/app` env var in Docker compose for path resolution (templates, static, HTML files).

### LLM Integration

Uses OpenRouter (`x-ai/grok-4.1-fast`) via the OpenAI SDK. The system prompt in `src/classgen/content/prompts.py` defines the lesson pack format. Only `OPENROUTER_API_KEY` is required for local dev.

## CI

GitHub Actions (`.github/workflows/ci.yml`): runs `pytest` + `ruff check` on push/PR to `main`/`master`. Uses Python 3.14.

## Key Patterns

- **In-memory fallback everywhere**: each data module checks `if not supabase:` and falls back to `_mem_*` dict operations.
- **Command routing**: `classgen.commands.router.handle_command()` returns `CommandResult | None`. `None` means "not a command, send to LLM".
- **Block format**: Lesson packs use `[BLOCK_START_TYPE]...[BLOCK_END]` markers. Tests mock `call_openrouter` to return these blocks.
- **Tests mock external services**: `call_openrouter`, Supabase, and Twilio are patched in tests. Patches target `classgen.api.*` modules where functions are used, not where they're defined.
- **Path resolution**: Use `APP_ROOT` env var for project root in Docker. Fallback to `Path(__file__).parents[3]` for local dev with src/ layout.

## Environment

Only `OPENROUTER_API_KEY` is required to run locally without Docker. See `.env.example` for the full template. Copy to `.env` before running.

Docker compose sets `SUPABASE_URL`, `SUPABASE_KEY`, `DATABASE_URL`, `REDIS_URL`, and `APP_ROOT` automatically.
