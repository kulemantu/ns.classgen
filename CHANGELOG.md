# Changelog

All notable changes to ClassGen are documented here.

---

## V3.0 -- Platform (2026-03-17)

ClassGen becomes a tool schools can subscribe to, with curriculum guidance, billing, admin dashboards, and printable worksheets.

### 3.0a -- Curriculum Assist
- **WAEC curriculum data** for 5 core subjects (Biology, Mathematics, Chemistry, Physics, English) across SS1-SS3 (~180 topics)
- **`suggest` command**: teachers see which topics they haven't covered yet for any class
- **`covered` command**: review lesson generation history per class
- **Content cache**: identical lesson requests skip the LLM and serve from cache -- saves tokens and response time
- **Lesson history**: every generated lesson is logged for curriculum tracking

### 3.0b -- Billing & Subscriptions
- **Three tiers**: Free (5 lessons/week), Premium (unlimited, NGN 2,000/mo), School (per-seat, NGN 5,000/mo)
- **Usage tracking**: lessons counted per week, teachers see remaining quota
- **Quota enforcement**: teachers on free tier get a friendly upgrade message when they hit the limit
- **Payment providers**: Paystack (card, USSD, bank transfer) and manual bank transfer with reference codes
- **Provider-agnostic**: `billing.py` abstracts payment behind a `PaymentProvider` interface

### 3.0c -- School Admin & Worksheets
- **School admin dashboard** at `/s/{slug}`: teacher count, total lessons, per-teacher stats
- **Printable worksheet generator** (`worksheet.py`):
  - Bingo vocabulary grids (configurable size)
  - Fill-in-the-blank with answer key on separate page
  - Cut-out flashcards (front/back layout for scissors)
- **School model** in database: schools, teacher association, admin phone

### 3.0d -- Multi-language
- **Automatic language detection**: system prompt responds in the teacher's language
- **Bilingual lesson packs**: request "in English and Yoruba" for dual-language output
- Supported: French, Yoruba, Hausa, Swahili, and any language the LLM handles

---

## V2.1 -- Parent & Student Layer (2026-03-16)

Extended the value chain beyond the classroom to parents and students.

- **Student progress tracking**: `progress Amina SS2` shows quiz scores across all homework codes
- **Class leaderboard**: `leaderboard MATH42` ranks students by score
- **Parent WhatsApp digest**: `subscribe parent +234... Amina SS2 Biology` for weekly updates
- **Study mode**: `study Photosynthesis` returns a concise LLM-generated recap with self-test questions
- **Outbound messaging module** (`messaging.py`): Twilio REST client for proactive WhatsApp messages

---

## V2.0 -- Teacher Profiles (2026-03-16)

Gave teachers a persistent identity and students a reference point.

- **WhatsApp registration**: `register Mrs. Okafor` creates a teacher profile
- **Public profile pages** at `/t/mrs-okafor`: name, school, class badges, homework code table
- **Class management**: `add class: SS2 Biology` organizes lessons by class
- **WhatsApp command router** (`commands.py`): extensible command matching with LLM fallthrough
- **Data layer refactor** (`db.py`): all database ops with in-memory fallback for local dev
- **Jinja2 templates**: shared `base.html` template for consistent lightweight pages

---

## V1.3 -- Stabilisation (2026-03-16)

Fixed all critical bugs that would block real teacher adoption.

### Critical fixes
- **WhatsApp session**: phone-number-based persistent session (was hourly window that reset mid-conversation)
- **Homework URL**: absolute URLs in WhatsApp messages (was relative/unclickable)
- **Message truncation**: long lessons send block-title summary + PDF (was silent truncation at 1600 chars)
- **Voice notes**: rejected gracefully (was sending placeholder text to LLM)
- **PDF Unicode**: 35+ character mappings including subscripts for chemical formulas (was 8, crashed on common characters)
- **Webhook security**: Twilio signature validation when auth token is configured

### Experience improvements
- **Web session persistence**: localStorage threadId survives page refresh
- **Session depth**: 10 messages of context (was 3, too shallow for clarification flow)
- **Lightweight background**: CSS gradient replaces Three.js (saved ~200KB, no more GPU lag on budget phones)
- **PDF headers**: show teacher's request + generation date (was generic "ClassGen Lesson Plan")
- **Clarifying questions**: asks for ALL missing fields at once (was one-at-a-time over 2G)

### Infrastructure
- CI pipeline (GitHub Actions: pytest + ruff)
- PDF cleanup on startup (24-hour TTL)
- `.dockerignore` for clean Docker builds
- `/health` endpoint for monitoring
- Docker Compose: app + Postgres + PostgREST + Redis

---

## V1.2 -- Homework Codes (2026-03-16)

Bridged the gap between classroom and home.

- **6-character homework codes** generated with every lesson (e.g., `MATH42`)
- **Student quiz page** at `/h/CODE`: homework instructions + 5-question auto-generated MCQ
- **Auto-grading**: correct/wrong highlighting, score display, inputs locked after submission
- **Teacher results dashboard** at `/h/CODE/results`: submission count, average score, per-question breakdown with progress bars
- **14-day code expiry**: codes automatically become invalid after two weeks

---

## V1.1 -- Content Depth (2026-03-16)

Made lesson packs good enough for a teacher to use tomorrow without editing.

- **5-block lesson structure**: OPENER (hook), EXPLAIN (concept + wow fact), ACTIVITY (timed, large-class-friendly), HOMEWORK (exercise-book-first), TEACHER_NOTES (expected answers, common mistakes, exam tips)
- **6 homework formats**: story problem, detective case, fill-in narrative, design challenge, exercise book game, journal entry
- **Curriculum awareness**: WAEC, NECO, Cambridge exam board detection from class level
- **System prompt**: complete rewrite for natural spoken language, specific activities, paper-first design

---

## V1.0 -- Foundation (2026-03-16)

Initial working prototype.

- FastAPI backend with Twilio WhatsApp webhook
- Web chat UI with block rendering and suggestion pills
- OpenRouter LLM integration (Grok 4.1 Fast)
- PDF lesson plan generation (FPDF2)
- Supabase session logging
- Basic 3-block lesson pack (Hook, Fact, Application)
