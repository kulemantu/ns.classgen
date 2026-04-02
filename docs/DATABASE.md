# ClassGen Database Architecture

## Overview

ClassGen uses Postgres 16 as its persistent store, accessed via PostgREST (which provides a REST API compatible with the Supabase Python client). Redis handles ephemeral data (batch job queues, session cache). An in-memory fallback exists for local development without Docker.

## Storage Strategy

| Data Type | Store | Rationale |
|---|---|---|
| Teachers, homework codes, quiz submissions, lesson history, schools, subscriptions | **Postgres** | Persistent, shareable, survives restarts. Homework codes may be shared across teachers if high-engagement. |
| Batch job queue + progress | **Redis** | Ephemeral (1-hour TTL), needs fast polling during generation. Loss on restart is acceptable. |
| Active thread mappings | **In-memory** | Per-session state, reconstructed on reconnect. |

### Why PostgREST instead of direct Postgres

The app uses the `supabase-py` client, which talks to PostgREST (a REST API over Postgres). This was chosen for:
- Drop-in migration path to Supabase Cloud if needed
- No ORM overhead — raw REST queries map directly to SQL
- Schema introspection serves as implicit API documentation

The migration runner (`migrations/runner.py`) connects directly to Postgres via `psycopg` since DDL operations aren't supported through PostgREST.

## Security

### `classgen_api` Role (2026-04-02)

PostgREST previously ran as the `postgres` superuser. This was replaced with a least-privilege `classgen_api` role:

```sql
CREATE ROLE classgen_api NOLOGIN;
GRANT USAGE ON SCHEMA public TO classgen_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO classgen_api;
```

The role has no `LOGIN`, no `CREATE`, no `DROP` — it can only read/write row data in existing tables. PostgREST authenticates requests using a JWT signed with `PGRST_JWT_SECRET` for `role: classgen_api`.

### Secrets

- `POSTGRES_PASSWORD` — strong random password, required by compose (fail-fast `?:` syntax)
- `PGRST_JWT_SECRET` — 48-char random string, required by compose
- `SUPABASE_ANON_KEY` — JWT with `{"role": "classgen_api"}` signed by `PGRST_JWT_SECRET`
- Local credentials stored in `.local/prod-credentials.env` (gitignored)

## Schema

Defined in `init.sql`, loaded by Postgres on first boot via `docker-entrypoint-initdb.d`.

### Tables

**Mutable (have `updated_at` + auto-update trigger):**

| Table | Primary Key | Purpose |
|---|---|---|
| `teachers` | `phone` | Teacher profiles (name, slug, school, classes) |
| `subscriptions` | `teacher_phone` | Billing tier + payment status |
| `lesson_cache` | `cache_key` | Cached LLM responses for identical lesson requests |
| `schools` | `slug` | School metadata (name, admin phone) |
| `push_subscriptions` | `endpoint` | Web push notification subscriptions |
| `parent_subscriptions` | `(parent_phone, teacher_phone, student_class)` | Parent digest subscriptions |

**Append-only (no `updated_at`, immutable once written):**

| Table | Primary Key | Purpose |
|---|---|---|
| `sessions` | `id` (uuid) | Chat conversation history |
| `homework_codes` | `code` (unique text) | Generated homework packs with lesson content + quiz |
| `quiz_submissions` | `id` (uuid) | Student quiz answers + scores |
| `lesson_history` | `id` (uuid) | Topic coverage tracking per teacher |
| `usage_log` | `id` (uuid) | Rate-limiting usage events |

**System:**

| Table | Purpose |
|---|---|
| `_migrations` | Tracks applied schema migrations |

### Timestamp Convention

- `created_at` — set by Postgres `DEFAULT now()`, never overwritten by application code. Represents when the row was first inserted.
- `updated_at` — set by Postgres trigger `set_updated_at()` on every `UPDATE`. Only on mutable tables.

Application code does **not** send `created_at` or `updated_at` in insert/upsert payloads — the database handles both. The in-memory fallback sets `created_at` manually since there's no DB default.

### Foreign Keys

Deliberate FK decisions:

| FK | Status | Rationale |
|---|---|---|
| `homework_codes.teacher_phone → teachers.phone` | **Removed** | Unregistered WhatsApp teachers generate lessons — FK would silently drop homework codes. `teacher_phone` is a soft reference. |
| `lesson_history.teacher_phone → teachers.phone` | **Removed** | Same reason — unregistered teachers can generate lessons. |
| `quiz_submissions.homework_code → homework_codes.code` | **Kept** | Submissions always reference an existing code (validated at API level). |
| `subscriptions.teacher_phone → teachers.phone` | **Kept** | Subscriptions are only created for registered teachers. |
| `parent_subscriptions.teacher_phone → teachers.phone` | **Kept** | Parent subscribe command validates teacher exists first. |

## Migrations

### Runner

`migrations/runner.py` — a ~75-line Python script that:
1. Connects directly to Postgres via `psycopg` (not PostgREST)
2. Creates `_migrations` tracking table on first run
3. Reads `DATABASE_URL` env var (fallback: constructs from `POSTGRES_PASSWORD`)
4. Applies numbered `.sql` files in order, skipping already-applied ones
5. Each migration runs in a single transaction — atomic apply or rollback

### Usage

```bash
# Docker (production)
docker exec classgen-app /app/.venv/bin/python -m migrations.runner
docker exec classgen-app /app/.venv/bin/python -m migrations.runner status

# Docker (dev)
docker compose exec app /app/.venv/bin/python -m migrations.runner
```

After applying migrations that add/remove columns, restart PostgREST to reload its schema cache:
```bash
docker restart classgen-rest
```

### Writing Migrations

1. Create `migrations/NNN_description.sql` (zero-padded number)
2. Write standard SQL (runs inside a transaction)
3. Use `IF NOT EXISTS` / `DROP ... IF EXISTS` to make migrations re-runnable where possible
4. Test locally: `docker compose exec app /app/.venv/bin/python -m migrations.runner`
5. Deploy: SCP file, rebuild image, run runner

### Applied Migrations

| # | File | Description |
|---|---|---|
| 001 | `001_baseline.sql` | Marker for initial `init.sql` schema |
| 002 | `002_add_updated_at.sql` | Added `updated_at` columns + `set_updated_at()` trigger to 6 mutable tables |

## Multi-Worker Considerations

The app runs with `--workers 2` (uvicorn). All persistent data goes through Postgres (shared), so workers don't diverge. Redis is also shared. The in-memory dicts (`_mem_*`) are per-worker but only used when Supabase is not configured (local dev without Docker).

## In-Memory Fallback

When `SUPABASE_URL` is not set, all `db.py` operations fall to in-memory Python dicts. This is for local development only — data is lost on restart and inconsistent across workers. The fallback is not a safety net for production DB outages; if PostgREST is down in production, writes are silently dropped (logged to stderr).
