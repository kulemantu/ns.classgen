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

## Architecture (V4.1)

Package layout under `src/classgen/` with layered dependencies: `core` ← `data` ← `services` ← `api`, `channels` ← `core`.

```
src/classgen/
  api/             FastAPI routers: app.py, chat.py, webhook.py, homework.py, teacher.py, profile.py, school.py, push.py, dev.py, schemas.py
  channels/        Rendering adapters: base.py (ABC), web.py, whatsapp.py, pdf.py + get_adapter() factory
  commands/        WhatsApp command router (router.py) + 16 handlers (handlers.py)
  content/         Prompts (text + JSON), curriculum data, PDF generator, worksheet generator
  core/            Domain models: models.py (LessonPack, typed blocks), parsers.py (dual JSON+block), feature_flags.py, billing.py
  data/            Persistence layer: 11 modules (sessions, teachers, homework, quiz, lessons, subscriptions, schools, parents, push, threads, client)
  integrations/    Third-party clients: Twilio, Redis queue
  services/        Business logic: LLM client (blocking + streaming + JSON), billing, notifications
  i18n.py          Locale/currency formatting
```

Root `main.py` exposes `app` via `from classgen.api.app import app`, and includes an `if __name__ == "__main__"` dev runner block that starts uvicorn with reload enabled when you run `python main.py`. Dockerfile CMD unchanged: `uvicorn main:app`.

### Channels (adapter pattern)

Three delivery channels share the same lesson generation core and command router. Each has a `ChannelAdapter` in `src/classgen/channels/`:

- **Web chat** (`POST /api/chat`, `POST /api/chat/stream`) — browser UI in `index.html`. `WebAdapter` returns structured JSON; frontend renders blocks as rich cards. SSE streaming available via `/api/chat/stream`.
- **WhatsApp** (`POST /webhook/twilio`) — Twilio webhook, returns TwiML. `WhatsAppAdapter` renders plain-text summary (block titles + homework link).
- **PDF** — `PDFAdapter` wraps `generate_pdf_from_markdown()` with structured LessonPack input.

When `FF_STRUCTURED_OUTPUT` is off, the legacy path (regex parsing of `[BLOCK_START_X]...[BLOCK_END]` markers) is used. When on, the LLM returns JSON, parsed into a `LessonPack` Pydantic model, and routed through channel adapters.

### Database

- **Postgres 16 + PostgREST v12** in both dev (Docker Compose) and production.
- **In-memory fallback** — when `SUPABASE_URL`/`SUPABASE_KEY` are unset, data modules use plain dicts. No DB needed to run locally without Docker.
- **supabase-py client** patches the internal `_postgrest` client for raw PostgREST compatibility (supabase-py appends `/rest/v1/` which raw PostgREST doesn't serve).
- **classgen_api** DB role — least-privilege (SELECT/INSERT/UPDATE/DELETE only). JWT must match `PGRST_JWT_SECRET`.
- Migrations in `migrations/` use psycopg directly against `DATABASE_URL` (not PostgREST).
- `APP_ROOT=/app` env var in Docker compose for path resolution (templates, static, HTML files).

### LLM Integration

Uses OpenRouter (`x-ai/grok-4.1-fast`) via the OpenAI SDK. Two system prompts in `src/classgen/content/prompts.py`: `CLASSGEN_SYSTEM_PROMPT` (legacy text blocks) and `CLASSGEN_JSON_SYSTEM_PROMPT` (structured JSON). Three LLM functions in `services/llm.py`: `call_openrouter` (blocking text), `call_openrouter_json` (blocking JSON with optional `response_format`), `stream_openrouter` (SSE streaming). Only `OPENROUTER_API_KEY` is required for local dev.

## CI

GitHub Actions (`.github/workflows/ci.yml`): runs `pytest` + `ruff check` on push/PR to `main`/`master`. Uses Python 3.14.

## Key Patterns

- **In-memory fallback everywhere**: each data module checks `if not supabase:` and falls back to `_mem_*` dict operations.
- **Command routing**: `classgen.commands.router.handle_command()` returns `CommandResult | None`. `None` means "not a command, send to LLM".
- **Dual lesson format**: Legacy `[BLOCK_START_TYPE]...[BLOCK_END]` markers (flags off) or structured JSON `LessonPack` (flags on). `parse_lesson_response()` in `core/parsers.py` tries JSON first, falls back to block regex. Both produce a `LessonPack` Pydantic model.
- **Feature flags**: 4 env-var flags in `core/feature_flags.py` — `FF_STRUCTURED_OUTPUT`, `FF_SSE_STREAMING`, `FF_JSON_RESPONSE_FORMAT`, `FF_EMBEDDED_QUIZ`. All default off. `structured_output` is the foundation; the other 3 depend on it. Use `flags.effective_*` properties for resolved state.
- **Tests mock external services**: `call_openrouter`, Supabase, and Twilio are patched in tests. Patches target `classgen.api.*` modules where functions are used, not where they're defined.
- **Path resolution**: Use `APP_ROOT` env var for project root in Docker. Fallback to `Path(__file__).parents[3]` for local dev with src/ layout.

## Environment

Only `OPENROUTER_API_KEY` is required to run locally without Docker. See `.env.example` for the full template. Copy to `.env` before running.

Docker compose sets `SUPABASE_URL`, `SUPABASE_KEY`, `DATABASE_URL`, `REDIS_URL`, and `APP_ROOT` automatically. Feature flags (`FF_*`) can be set in `docker-compose.override.yml` (gitignored) for local dev.

**Important**: After running DDL migrations, always restart PostgREST (`docker compose restart rest`) to refresh its schema cache.
