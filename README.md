# ClassGen

AI lesson pack generator for African secondary school teachers. Send a topic on WhatsApp or the web UI, get a structured, ready-to-teach lesson pack with an opener, explanation, classroom activity, exercise-book homework, and teacher notes.

Built for classrooms of 30-60 students with exercise books, pens, and a chalkboard. No projectors, no internet, no printouts required.

## Features

- **Structured lesson packs** — 5-block format (Opener, Explain, Activity, Homework, Teacher Notes) designed to be read aloud or paraphrased
- **WhatsApp-native** — teachers interact via Twilio WhatsApp; works on any phone
- **Web chat UI** — browser-based chat with structured lesson cards, detail overlays, and SSE streaming
- **Homework codes** — 6-character codes (e.g. `MATH42`) with auto-generated 5-question MCQ quizzes, student self-grading, and teacher result dashboards
- **Exam-board aware** — auto-detects WAEC/NECO (Nigeria), KNEC/KCSE (Kenya), Cambridge/IGCSE from class level
- **Curriculum suggestions** — WAEC syllabus data for Biology, Mathematics, Chemistry, Physics, English (SS1-SS3); suggests uncovered topics
- **Multi-language** — responds in the teacher's language (Swahili, Yoruba, Hausa, French, etc.); bilingual packs on request
- **Multi-currency** — Babel-backed i18n with locale detection from phone country code (NGN, KES, USD)
- **PDF generation** — downloadable lesson PDFs with Unicode support and 24-hour auto-cleanup
- **Billing** — free tier (5 lessons/week), Premium, and School plans with Paystack integration
- **Teacher profiles** — public pages, class management, lesson history
- **School admin** — dashboards with teacher rosters and engagement stats
- **Push notifications** — browser alerts when students submit quizzes

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn |
| LLM | OpenRouter (`x-ai/grok-4.1-fast`) via OpenAI SDK |
| Database | Postgres 16 + PostgREST v12 (supabase-py client), in-memory fallback for local dev |
| Messaging | Twilio WhatsApp |
| PDF | fpdf2 |
| i18n | Babel |
| Payments | Paystack |
| Frontend | Vanilla JS, Tailwind CDN |
| Deployment | Docker, Caddy (auto-HTTPS), uv |
| CI | GitHub Actions (pytest + ruff) |

## Quick Start

```bash
# Clone and install
git clone https://github.com/kulemantu/ns.classgen.git
cd ns.classgen
uv sync

# Configure
cp .env.example .env
# Edit .env with your API keys (only OPENROUTER_API_KEY is required for local dev)

# Run
uv run python main.py
# Open http://localhost:8000
```

No Supabase or Twilio needed for local development — the app falls back to in-memory storage and the web chat UI.

### Docker

```bash
# Local dev (app + Postgres + PostgREST + Redis)
docker compose up -d

# Production (app + Caddy auto-HTTPS + Redis, Supabase Cloud)
cd deploy
cp .env.prod.example .env.prod
# Edit .env.prod
python deploy.py setup
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | LLM provider key |
| `SUPABASE_URL` | Prod | Supabase project URL |
| `SUPABASE_KEY` | Prod | Supabase anon key |
| `TWILIO_ACCOUNT_SID` | WhatsApp | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | WhatsApp | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | WhatsApp | Twilio WhatsApp number |
| `PAYSTACK_SECRET_KEY` | Payments | Paystack secret key |
| `VAPID_PRIVATE_KEY` | Push | Web push private key |
| `VAPID_PUBLIC_KEY` | Push | Web push public key |

See `.env.example` for the full template.

## WhatsApp Commands

| Command | Description |
|---|---|
| `SS2 Biology: Photosynthesis` | Generate a lesson pack |
| `register Mrs. Okafor` | Create teacher profile |
| `add class: SS2 Biology` | Add a class |
| `suggest SS2 Biology` | See uncovered curriculum topics |
| `covered SS2 Biology` | See topics already taught |
| `study Photosynthesis` | Quick revision recap for students |
| `results MATH42` | Quiz submission summary |
| `leaderboard MATH42` | Top-scoring students |
| `progress Amina SS2` | Student quiz history |
| `my codes` | List recent homework codes |
| `subscribe parent +234... Amina SS2 Biology` | Parent progress updates |
| `new` | Start a new session |
| `help` | All commands |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web chat UI |
| `GET` | `/health` | Health check |
| `GET` | `/terms` | Terms & Privacy page |
| `GET` | `/api/config` | Feature flag state (for frontend) |
| `POST` | `/api/chat` | Web chat (JSON) |
| `POST` | `/api/chat/stream` | Web chat (SSE streaming) |
| `POST` | `/webhook/twilio` | WhatsApp webhook (TwiML) |
| `GET` | `/h/{code}` | Student quiz page |
| `POST` | `/h/{code}/submit` | Submit quiz answers |
| `GET` | `/h/{code}/results` | Teacher results dashboard |
| `GET` | `/t/{slug}` | Public teacher profile |
| `GET` | `/s/{slug}` | School admin dashboard |
| `POST` | `/api/push/subscribe` | Register push notifications |

## Project Structure

```
src/classgen/
  api/               FastAPI routers (chat, webhook, homework, teacher, school, push, dev)
  channels/          Rendering adapters: web (JSON), whatsapp (plain text), pdf
  commands/          WhatsApp command router + 16 command handlers
  content/           System prompts (text + JSON), curriculum data, PDF generator, onboarding config
  core/              Domain models (LessonPack, blocks), dual parser, feature flags, billing tiers
  data/              Persistence: 11 modules with Supabase + in-memory fallback
  integrations/      Third-party clients: Twilio, Redis queue
  services/          Business logic: LLM client (blocking/streaming/JSON), billing, notifications
  i18n.py            Locale/currency formatting

main.py              One-liner re-export: from classgen.api.app import app
index.html           Web chat UI (lesson cards, SSE streaming, intro overlay)
homework.html        Student quiz page (auto-grading)
terms.html           Terms & Privacy page
templates/           Jinja2 templates (teacher profiles, school admin)
migrations/          SQL migrations (psycopg, run via migrations.runner)
deploy/              Production Docker Compose + deploy script
tests/               350+ pytest tests
```

**Dependency direction:** `core` <-- `data` <-- `services` <-- `api`. `channels` imports `core` only.

## Testing

```bash
uv run pytest tests/ -v           # Run all tests (350+)
uv run ruff check .               # Lint
uv run ruff format .              # Format
uv run pyright                    # Type check
```

CI runs pytest + ruff on push/PR to `main`/`master` via GitHub Actions. See [CONTRIBUTING.md](CONTRIBUTING.md) for PR guidelines.

## Deployment

```bash
cd deploy
python deploy.py check    # Validate environment
python deploy.py setup    # First-time build + start
python deploy.py update   # Pull + rebuild + restart
python deploy.py status   # Health check
python deploy.py logs     # Tail logs
python deploy.py test     # Local build + smoke test + teardown
```

Production stack: nginx-proxy (auto-HTTPS) -> FastAPI -> Postgres 16 + PostgREST + Redis. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

**After DDL migrations**, always restart PostgREST: `docker compose restart rest`

## License

All rights reserved.
