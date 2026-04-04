# ClassGen Build Log

## Current State (V1.3 -- Stabilisation complete)

- FastAPI backend with Twilio WhatsApp webhook + web chat UI
- 5-block lesson pack: OPENER, EXPLAIN, ACTIVITY, HOMEWORK, TEACHER_NOTES
- PDF generation via fpdf2 (with subtitle + date, expanded Unicode sanitization)
- Supabase session logging (with in-memory fallback for local dev)
- OpenRouter LLM (Grok 4.1 Fast)
- Homework code system: quiz generation, student submission, teacher results dashboard
- Twilio webhook signature validation (when TWILIO_AUTH_TOKEN set)

## What's Done

### V1.0 -- Foundation
- WhatsApp webhook (Twilio) + web chat UI
- 3-block lesson pack (Hook, Fact, Application)
- PDF download, Supabase session logging, OpenRouter integration

### V1.1 -- Content Depth
- Restructured to 5 blocks: OPENER, EXPLAIN, ACTIVITY, HOMEWORK, TEACHER_NOTES
- Exercise-book-first homework formats (stories, games, detective cases, design challenges, journal entries)
- Curriculum/exam board awareness (WAEC, NECO, Cambridge)
- Repo scaffolding: uv, git, spec/ docs/ structure, Dockerfile on uv

### V1.2 -- Homework Codes (partial)
- 6-char code generated per lesson pack (e.g., `MATH42`)
- Student quiz page at `/h/{CODE}` -- homework instructions + 5-question MCQ
- Quiz auto-generated from lesson content via second LLM call
- Student enters name + class, submits answers, gets auto-graded with correct/wrong highlighting
- Teacher results dashboard at `/h/{CODE}/results` -- stats, per-question breakdown, submissions table
- Results data API at `/api/h/{CODE}/results`
- **Still TODO:** teacher results summary via WhatsApp (outbound Twilio), homework code expiry

### V1.3 -- Stabilisation
- **WhatsApp session:** phone-number-based persistent session (was hourly window). Send "new" to reset.
- **WhatsApp homework URL:** absolute URL (was relative/broken)
- **WhatsApp message truncation:** long lessons send block-title summary + PDF attachment (was raw truncation)
- **Voice notes:** rejected gracefully (was passing placeholder to LLM)
- **PDF Unicode:** expanded sanitizer to 23 characters -- degree, naira, pi, arrows, etc. (was 8)
- **PDF header:** shows teacher's request as subtitle + generation date (was generic "ClassGen Lesson Plan")
- **Twilio validation:** RequestValidator when auth token configured (was open to any HTTP client)
- **Web session:** threadId persisted in localStorage (was Math.random on every page load)
- **Session history:** 10 messages (was 3 -- too shallow for clarification flow)
- **Background:** CSS animated gradient (was Three.js with 90 glass-material meshes, ~200KB heavier)
- **Clarifying questions:** prompt asks for ALL missing fields at once (was one-at-a-time)
- **Cleanup:** removed BLOCK_TYPE_LABELS, legacy block icons, orphan images, docker-compose.yml, unused three.min.js; created .dockerignore; added /health endpoint; fixed dummy API key fallback
- **In-memory fallback:** homework codes, quiz submissions, and results work without Supabase for local dev
- **Dev seed endpoint:** `POST /api/dev/seed` creates mock homework data for testing

### Browser-tested flows (2026-03-16)
- Home page: CSS gradient loads, chat input works, breadcrumb renders, error handling displays gracefully
- Homework page `/h/TEST01`: loads homework details, renders 5 quiz questions, form validation works
- Quiz submission: grading correct (4/5), green/red highlighting, score card, inputs disabled after submit
- Results dashboard `/h/TEST01/results`: stats cards (students, avg score, questions), per-question % bars, submissions table
- 404 handling: homework and results pages show clear "not found" messages
- Health endpoint: returns `{"status": "ok"}`
- Session persistence: localStorage threadId survives page reload

## Architecture

```
main.py          -- FastAPI app, endpoints, system prompt, quiz generation, WhatsApp summary
utils.py         -- OpenRouter client, Supabase client (with in-memory fallback), homework/quiz CRUD
pdf_generator.py -- FPDF2 PDF generation, latin-1 sanitization, subtitle/date header
index.html       -- Web chat UI, CSS gradient background, block rendering, suggestion pills
homework.html    -- Student quiz page (~5KB, 2G-friendly)
results.html     -- Teacher results dashboard (stats, per-question breakdown, submissions)
```

### Docker Compose (local dev)

```
docker compose up -d
docker compose exec app /app/.venv/bin/python -m migrations.runner
```

Services:
- **app** (port 8000) -- FastAPI app, built from Dockerfile, 2 uvicorn workers
- **db** (port 5432) -- Postgres 16, initialized with `init.sql` schema
- **rest** (port 3000) -- PostgREST v12, provides REST API for Supabase client, `classgen_api` role
- **redis** (port 6379) -- Redis 7 with AOF persistence, 128MB LRU cache

The app auto-connects to PostgREST as its Supabase backend via env vars set in compose. Migrations must be run after first boot or schema changes.

### Additional fixes (2026-03-16, session 2)

- **PDF Unicode subscripts:** added subscript/superscript digit mappings (CO2, H2O, C6H12O6 render correctly)
- **PDF x-position safety:** explicit page width + `set_x(l_margin)` before every `multi_cell` (fixes "Not enough horizontal space" crash)
- **PDF block regex:** changed terminator from `(?=\n\n|\Z)` to `(?=\nTitle:|\Z)` for more robust block detection
- **In-memory fallback:** homework codes/quiz submissions work without Supabase for local dev
- **Dev seed endpoint:** `POST /api/dev/seed` creates mock homework data for testing (disabled when Supabase configured)

### LLM-tested flows (2026-03-16)
- "SS2 Biology: Photosynthesis" -- 5 blocks generated, detective case homework, quiz auto-generated, quiz submission graded 5/5, results dashboard showed per-question breakdown
- "SS1 Mathematics: Area of a circle" -- 5 blocks, story problem homework, PDF generated correctly (2 pages), subscripts rendered

### V1.2/V1.3 completion (2026-03-16, session 3)
- **Homework code expiry:** 14-day TTL via `_is_expired()` check on retrieval in `utils.py`
- **PDF cleanup:** lifespan startup event deletes PDFs older than 24 hours (replaced deprecated `on_event`)
- **CI pipeline:** `.github/workflows/ci.yml` with pytest + ruff lint on push/PR to main/master
- **Ruff added:** dev dependency, all lint issues fixed (unused imports removed)
- **Docker Compose:** app + Postgres 15 + PostgREST v12 + Redis 7 (created in session 2)

### V2.0 -- Teacher Profiles (2026-03-16, session 4)

**Shared module extraction (cross-cutting refactor):**
- `db.py` -- all Supabase/Postgres operations with in-memory fallback. Sessions, homework codes, quiz submissions, teachers. Consistent `save_X/get_X/list_X` patterns.
- `commands.py` -- WhatsApp command router. Matches text against registered commands, falls through to LLM if no match. Returns structured `CommandResult`.
- `utils.py` -- slimmed to OpenRouter client + `generate_homework_code()` only
- `templates/base.html` -- shared Jinja2 base template (styles, layout, footer)
- `templates/profile.html` -- teacher profile page extending base

**Teacher features:**
- Registration via WhatsApp: `register Mrs. Okafor` -> creates teacher record, generates slug, returns profile URL
- Profile page at `/t/{slug}`: name, school, class badges, homework codes table with links
- Class management: `add class: SS2 Biology` -> adds to teacher's class list
- Homework codes linked to teacher via `teacher_phone` field
- Commands: `help`, `register`, `my page`, `add class`, `my codes`, `results CODE`, `new`

**Browser-tested (2026-03-16):**
- Profile page `/t/mrs-okafor`: name, school, class badges, homework table with links
- Profile 404 for unknown slugs
- All 5 WhatsApp commands via webhook: help, register, my page, add class, reset
- Dynamic profile creation via `register` command -> immediately visible at `/t/mr-adeyemi`

### V3.0 -- Platform (2026-03-17)

**3.0a -- Curriculum Assist:**
- `curriculum.py` -- WAEC topic lists for 5 subjects, ~180 topics
- `suggest` / `covered` commands for topic guidance
- Content cache: identical lesson requests skip LLM
- Lesson history: auto-logged for coverage tracking

**3.0b -- Billing:**
- `billing.py` -- usage tracking, subscription tiers (Free/Premium/School), quota enforcement
- Paystack + bank transfer payment providers (provider-agnostic abstraction)
- Usage check integrated into webhook handler before LLM calls

**3.0c -- School Admin & Worksheets:**
- School admin dashboard at `/s/{slug}` with teacher stats
- `worksheet.py` -- bingo grids, fill-in-the-blank, flashcard cut-outs
- `db.py` -- school CRUD operations

**3.0d -- Multi-language:**
- System prompt detects teacher's language automatically
- Bilingual lesson packs on request

### Architecture (V3.1)

```
main.py              -- FastAPI app, endpoints, system prompt, LLM orchestration, usage quota
commands.py          -- WhatsApp command router (16 commands)
db.py                -- Data access layer (10 tables, Supabase/PostgREST + in-memory fallback)
utils.py             -- OpenRouter LLM client + homework code generator
billing.py           -- Usage tracking, subscription tiers, payment providers (Paystack, bank transfer)
curriculum.py        -- WAEC topic lists, suggest/covered logic
jobs.py              -- Async batch job queue (Redis + in-memory fallback)
messaging.py         -- Outbound Twilio WhatsApp messaging
pdf_generator.py     -- Lesson PDFs + combined week-pack PDFs
worksheet.py         -- Printable worksheets (bingo, fill-in-blank, flashcards)
migrations/          -- SQL migrations + runner (psycopg direct to Postgres)
templates/           -- Jinja2: base.html, profile.html, admin.html
index.html           -- Web chat UI
homework.html        -- Student quiz page
results.html         -- Teacher results dashboard
init.sql             -- Base schema + classgen_api role (loaded by Postgres on first boot)
```

See [DATABASE.md](DATABASE.md) for schema details, migration workflow, and storage strategy.

### V3.1 -- Production Database & Infrastructure (2026-04-02)

**Database layer:**
- Added Postgres 16 + PostgREST to production (was in-memory only, breaking homework codes)
- Created `classgen_api` least-privilege role (was running PostgREST as `postgres` superuser)
- Generated strong Postgres password + JWT secret (was using hardcoded defaults)
- Compose now requires `--env-file deploy/.env.prod` (fail-fast on missing secrets)

**Migration tooling:**
- `migrations/runner.py` -- lightweight SQL migration runner (~75 lines, `psycopg` direct connection)
- Tracks applied migrations in `_migrations` table
- Migration 002: added `updated_at` columns + auto-update triggers to 6 mutable tables

**Timestamp semantics fix:**
- `created_at` now set by DB `DEFAULT now()`, never sent by application code on upserts
- `updated_at` auto-managed by `set_updated_at()` Postgres trigger on UPDATE
- Fixed: `save_teacher()`, `save_subscription()`, `cache_lesson()`, `save_school()`, `save_parent_subscription()`, `save_homework_code()`, `log_lesson_generated()`, `log_usage()` -- all stopped overwriting `created_at` on upsert

**Foreign key cleanup:**
- Dropped FKs on `homework_codes.teacher_phone` and `lesson_history.teacher_phone` -- unregistered WhatsApp teachers could generate lessons but FK violations silently dropped homework codes

**Frontend:**
- Added emoji favicon (globe SVG, matching dater.world)
- Breadcrumbs truncated to ~20 chars, limited to first 5 items (was full message text, last 4)

**Bug fix:**
- OpenRouter API key rotated on production (was returning 401 "User not found")

### V4.0 — Project Restructure (2026-04-04, PR #1)

**Restructure to `src/classgen/` package:**
- Split 12 root Python files into 9 sub-packages under `src/classgen/`
- Function-by-function verification: all 80+ functions ported identically
- Found and fixed 2 prompt regressions (agent softened wording in system prompt)
- 163 tests (102 new), 58% coverage, ruff clean
- Old root `.py` files deleted — all tests pass without them

**Docker staging fixes (v4.0-staging branch):**
- Dockerfile: two-step `uv sync` for `src/` layout (`--no-install-project` first, then `--no-editable`)
- Path resolution: `APP_ROOT=/app` env var for templates/static/HTML paths (non-editable installs put `__file__` in `site-packages/`)
- JWT: regenerated for `classgen_api` role (was signed for `anon` role)
- CI: Python 3.14 (was 3.12)

**Staging test results:** 19/19 HTTP checks pass on Docker Compose, covering health, teacher registration, lesson generation, homework+quiz flow, PDF download, CSV export, WhatsApp webhook.

## What's Next

See [ROADMAP.md](ROADMAP.md) for V4.1-V4.4 phases.

**Immediate:** Merge v4.0-staging → master → deploy to production.

**Next phase (V4.1):** Structured JSON output from LLM + channel adapters + SSE streaming. See [DESIGN-v4-structured-output.md](DESIGN-v4-structured-output.md).
