# Contributing to ClassGen

## Quick Start

```bash
git clone https://github.com/kulemantu/ns.classgen.git
cd ns.classgen
uv sync
cp .env.example .env         # Only OPENROUTER_API_KEY is required
uv run python main.py        # http://localhost:8000
uv run pytest tests/ -v      # 350+ tests
```

## Before You Push

Every PR must pass these checks:

```bash
uv run ruff check .           # Lint — zero errors
uv run ruff format --check .  # Formatting — zero diffs
uv run pytest tests/ -v       # Tests — all green
```

If you're touching types: `uv run pyright`

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

feat(api):      new endpoint or feature
fix(web):       bug fix in the frontend
refactor(data): internal restructure, no behavior change
test:           new or updated tests only
docs:           documentation only
chore:          tooling, CI, deps
```

Sign off with:
```
Signed-off-by: Your Name <your@email.com>
```

## Pull Requests

- **Branch from `master`**, PR back to `master`
- **Keep PRs focused** — one concern per PR (don't mix features with refactors)
- **Include tests** for new functionality
- **Update docs** if you add endpoints, flags, or change architecture
- CI must pass before merge

### PR title format

Same as commit message: `type(scope): description`

## Where to Add Things

| I want to... | Edit this |
|---|---|
| Add an API endpoint | `src/classgen/api/` — create or extend a router |
| Add a WhatsApp command | `src/classgen/commands/handlers.py` + `router.py` |
| Change the LLM prompt | `src/classgen/content/prompts.py` |
| Add a database table | `migrations/NNN_description.sql` + `src/classgen/data/` |
| Add a domain model | `src/classgen/core/models.py` |
| Change billing tiers | `src/classgen/core/billing.py` |
| Add a channel adapter | `src/classgen/channels/` |
| Change the web UI | `index.html` |

## Architecture

```
core  <--  data  <--  services  <--  api
                                     channels  <--  core
```

- **core/** — Pure data models (Pydantic, dataclasses). No I/O.
- **data/** — Persistence. Each module has Supabase + in-memory fallback.
- **services/** — Business logic. Orchestrates data + LLM.
- **api/** — FastAPI routers. Thin — delegates to services.
- **channels/** — Renders a `LessonPack` for web, WhatsApp, or PDF.

See [CLAUDE.md](CLAUDE.md) for detailed architecture docs.

## Feature Flags

All V4.1+ features are gated behind env-var flags (default off):

| Flag | What it does |
|---|---|
| `FF_STRUCTURED_OUTPUT` | LLM returns JSON instead of text blocks |
| `FF_SSE_STREAMING` | Web chat streams blocks via SSE (requires structured_output) |
| `FF_JSON_RESPONSE_FORMAT` | Passes `response_format` to OpenRouter API |
| `FF_EMBEDDED_QUIZ` | Quiz embedded in lesson JSON (skips second LLM call) |

Enable locally via `docker-compose.override.yml` (gitignored):

```yaml
services:
  app:
    environment:
      - FF_STRUCTURED_OUTPUT=true
      - FF_SSE_STREAMING=true
```

## Testing Conventions

- **Patches target where functions are used**, not where they're defined: `@patch("classgen.api.chat.call_openrouter")` not `@patch("classgen.services.llm.call_openrouter")`
- **In-memory fallback** activates when Supabase env vars are unset (no DB needed for tests)
- **`tests/conftest.py`** has an autouse fixture that bypasses the onboarding guard. If you're testing onboarding, mock `is_onboarded` explicitly in your test.
- **`tests/fixtures.py`** has shared sample data (`SAMPLE_LESSON_JSON`, `SAMPLE_LESSON_BLOCKS`)

## Docker Dev Stack

```bash
docker compose up -d                              # App + Postgres + PostgREST + Redis
docker compose exec app /app/.venv/bin/python -m migrations.runner   # Run migrations
docker compose restart rest                        # After DDL migrations
docker compose logs -f app                         # Tail logs
```

Feature flags in local Docker: create `docker-compose.override.yml` (gitignored).

## Questions?

Open an issue or check the existing docs:
- [CLAUDE.md](CLAUDE.md) — Architecture reference
- [docs/ROADMAP.md](docs/ROADMAP.md) — Feature roadmap
- [docs/DATABASE.md](docs/DATABASE.md) — Schema and migrations
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Production deployment
