# ClassGen

AI lesson pack generator for African secondary school teachers. Send a topic on WhatsApp or the web UI, get a structured, ready-to-teach lesson pack with an opener, explanation, classroom activity, exercise-book homework, and teacher notes.

Built for classrooms of 30-60 students with exercise books, pens, and a chalkboard. No projectors, no internet, no printouts required.

## Features

- **Structured lesson packs** — 5-block format (Opener, Explain, Activity, Homework, Teacher Notes) designed to be read aloud or paraphrased
- **WhatsApp-native** — teachers interact via Twilio WhatsApp; works on any phone
- **Web chat UI** — browser-based alternative with Three.js background and block rendering
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
| Database | Supabase (PostgreSQL), in-memory fallback for local dev |
| Messaging | Twilio WhatsApp |
| PDF | fpdf2 |
| i18n | Babel |
| Payments | Paystack |
| Frontend | Vanilla JS, Three.js, Tailwind CDN |
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
| `POST` | `/api/chat` | Web chat (JSON) |
| `POST` | `/webhook/twilio` | WhatsApp webhook (TwiML) |
| `GET` | `/h/{code}` | Student quiz page |
| `POST` | `/h/{code}/submit` | Submit quiz answers |
| `GET` | `/h/{code}/results` | Teacher results dashboard |
| `GET` | `/t/{slug}` | Public teacher profile |
| `GET` | `/s/{slug}` | School admin dashboard |
| `POST` | `/api/push/subscribe` | Register push notifications |

## Project Structure

```
main.py              FastAPI app, endpoints, system prompt, lesson generation
commands.py          WhatsApp command router (18+ commands)
db.py                Data access layer (Supabase + in-memory fallback)
utils.py             OpenRouter client, homework code generation
billing.py           Subscription tiers, usage tracking, Paystack
i18n.py              Babel-backed locale detection and currency formatting
curriculum.py        WAEC syllabus data and topic suggestion engine
pdf_generator.py     FPDF2 lesson PDF generation
notifications.py     Web push notifications (VAPID/pywebpush)
messaging.py         Outbound Twilio WhatsApp messaging
jobs.py              Async batch job queue (in-memory or Redis)
worksheet.py         Printable worksheet generation (bingo, flashcards)

index.html           Web chat UI (Three.js, block rendering)
homework.html        Student quiz page (auto-grading)
results.html         Teacher results dashboard

site/index.html      Product guide / landing page
templates/           Jinja2 templates (teacher profiles, school admin)
deploy/              Production Docker Compose + deploy script
tests/               pytest suite (endpoints, utils, PDF, deploy)
```

## Testing

```bash
uv run pytest tests/ -v           # Run all tests
uv run pytest tests/ --cov=.      # With coverage
uv run ruff check .               # Lint
```

CI runs automatically on push/PR to `main` or `master` via GitHub Actions.

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

Production stack: Caddy (auto-HTTPS via Let's Encrypt) -> FastAPI (2 workers) -> Supabase Cloud + Redis.

## License

All rights reserved.
