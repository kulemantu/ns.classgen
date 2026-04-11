# ClassGen Product Roadmap

Confidential -- Working Draft | March 2026

---

## The Content Philosophy

ClassGen is not a chatbot. It is a **content design engine** that produces structured, ready-to-teach lesson packs. The quality of the content is the entire product. Every feature we build exists to make the generated content more useful, more engaging, and easier for a teacher to pick up and use immediately.

Three principles guide every content decision:

1. **Paper-first.** Every lesson pack must work perfectly when read aloud or written on a chalkboard. Technology is an enhancement layer, never a requirement.
2. **Teacher as performer.** The teacher is the delivery mechanism. Our content gives them material to *perform* -- hooks, stories, challenges, surprises -- not walls of text to dictate.
3. **Exercise book is the student's platform.** For most students, their exercise book is the only tool they take home. Homework must be designed to be completed in an exercise book with nothing else.

---

## Content Strategy

### A. In-Class Content

The lesson pack is structured as a **lesson flow** -- each section maps to a phase of the class period.

#### 1. Opener (first 2 minutes)

Purpose: break the pattern, create curiosity, get students leaning in.

Formats that work:
- **"What if" scenario** -- "What if gravity stopped for 10 seconds right now? What happens to the chalk I just threw?" Then connect to the lesson.
- **Visible demonstration** -- teacher does something unexpected (drops two objects, draws an optical illusion, reads a surprising statistic).
- **Challenge question** -- "I'll give you 30 seconds. Without looking at your notes, can anyone tell me why the sky is blue? No? By the end of this class, every one of you will know."
- **Story cold open** -- Start mid-story: "In 1928, a scientist came back from holiday to find mould growing on his experiment. He almost threw it away..."

What does NOT work: "Today we are going to learn about X." That is the opposite of a hook.

#### 2. Core Concept with Wow Factor

Purpose: explain the concept in plain language while weaving in encyclopedia-level depth that makes students feel like they are learning secrets, not syllabus.

The explanation should be:
- Plain enough for a teacher to paraphrase naturally
- Contain at least one "wow fact" embedded in the explanation (not separated)
- Connect to something students already know or experience daily
- Include a simple analogy the teacher can use

#### 3. Classroom Activity (10-15 minutes)

Purpose: students DO something. The activity is not the teacher talking -- it is students moving, writing, debating, building, or competing.

Constraints to design for:
- **Large classes** (30-60 students)
- **Minimal materials** (exercise books, pens, chalk, maybe a ruler)
- **Limited space** (fixed desks in many schools)

Formats that work:
- **Group Challenge** -- Split into teams of 4-6. Each team solves a problem or builds something. Teams present in 60 seconds.
- **Relay Race** -- Teams line up. First person answers Q1 on the board, tags the next person. First team to finish correctly wins.
- **Think-Pair-Share** -- Individual thinking (1 min), discuss with partner (2 min), selected pairs share with class.
- **Class Debate** -- Split class in two. One side argues for, one against. Teacher moderates. Works for any topic with two perspectives.
- **Gallery Walk** -- Groups create a poster (on paper/cardboard). Posters go up on walls. Class walks around, each group explains their poster to visitors.
- **Quick Quiz Battle** -- Teacher reads questions. Students write answers on mini-whiteboards or hold up fingers (A=1, B=2, C=3, D=4).

Every activity must include: group size, timing breakdown, clear rules, expected outcome.

#### 4. Teacher Notes (private)

Purpose: give the teacher confidence. Not shown to students.

Includes:
- Expected answers for the activity
- Common mistakes students make on this topic
- Quick assessment: "If students can answer X, they understood the lesson"
- One sentence on how this connects to the next lesson
- Optional: exam-style question from WAEC/NECO past papers

---

### B. At-Home Content -- Exercise Book (No Tech)

This is the most important content innovation. The default homework format should be **engaging enough that students want to do it**, using only their exercise book and a pen.

#### Format 1: Story Problem

A narrative where the student IS a character. To complete the story, they must apply what they learned.

> *"You are an engineer hired to design a water tank for a village. The village has 200 people who each use 20 litres per day. The tank is cylindrical with a radius of 2 metres. Using what you learned about volume of cylinders, calculate: (a) how tall the tank needs to be, (b) draw the tank with dimensions labelled, (c) write a one-paragraph report to the village chief explaining your design."*

Why it works: the student is solving a real problem, not "Question 3b."

#### Format 2: Detective Case File

Present evidence. Student uses lesson concepts to solve the mystery.

> *"Case #47: The school garden's plants are dying on one side but thriving on the other. Evidence: (1) Both sides get the same water. (2) One side is near the generator room. (3) Soil samples show different pH levels. Using your knowledge of acids, bases, and pH, write a detective report: What is killing the plants? What is the chemical cause? Recommend a solution."*

#### Format 3: Fill-in Narrative

A story with deliberate gaps that require subject knowledge to complete.

> *"In _______ (year), a scientist named _______ heated mercury oxide and noticed it produced a gas that made flames burn _______. He called it 'dephlogisticated air', but today we call it _______. The chemical equation for this reaction is: _______. This discovery was important because _______."*

Good for: revision, factual recall, building connections between facts.

#### Format 4: Design Challenge

Student creates something in their exercise book.

> *"Design a poster explaining photosynthesis to a JSS1 student. Your poster must include: a labelled diagram, the word equation, 3 fun facts, and one real-world example. Use one full page of your exercise book. Colour is optional but encouraged."*

#### Format 5: Exercise Book Game

A simple game the student can play alone or with a sibling/friend, drawn in their exercise book.

> *"Draw a 4x4 grid in your exercise book. In each square, write one of these vocabulary words: [16 words]. Your parent or sibling reads the definition, you cross out the matching word. First to get 4 in a row wins. Play 3 rounds and record your scores."*

Other game formats:
- **Path game** -- Draw a winding path with 15 squares. Each square has a question. Move forward if correct (self-check with answer key at the bottom, folded over).
- **Top Trumps cards** -- Draw 6 cards on a page, each with a different [element / historical figure / organism]. Write stats for each. Compare with a classmate the next day.
- **Comic strip** -- 6 panels explaining a process (water cycle, cell division, a historical event). Must include speech bubbles with correct terminology.

#### Format 6: Letter or Journal Entry

Write from a perspective.

> *"Write a one-page diary entry as Marie Curie on the day she discovered radium. Include: what experiment you ran, what you observed, why you think it matters, and one worry you have about the future of your discovery. Use at least 4 scientific terms from today's lesson."*

---

### C. At-Home Content -- Tech-Enabled (When Available)

For students and teachers with smartphone/internet access. These are **enhancement layers** on top of the exercise book homework -- never replacements.

#### Homework Codes (V1.2)

How it works:
1. Teacher generates a lesson pack via WhatsApp or web.
2. ClassGen returns the lesson pack + a **6-character homework code** (e.g., `MATH42`).
3. Teacher writes the code on the board or tells students.
4. Students who have access visit `classgen.ng/h/MATH42` on any phone browser.
5. The page shows:
   - The exercise book homework instructions (same as what the teacher read out)
   - A **5-question quick quiz** based on the lesson (multiple choice, auto-graded)
   - Student enters their name and class -- no account needed
6. Teacher sees a simple dashboard: how many students completed, average score, which questions were hardest.

Key design rules:
- The code page must load fast on 2G/3G connections (< 100KB).
- The quiz is SUPPLEMENTARY. The exercise book homework is the primary assignment.
- No login required for students. Name + class is enough.
- Teacher accesses results via WhatsApp (ClassGen sends a summary message) or web.

#### Teacher Profile Pages (V2.0)

A simple public page for each teacher: `classgen.ng/t/mrs-okafor`

Shows:
- Teacher name, school, subjects taught
- Current homework codes (last 2 weeks)
- Calendar view of recent lessons generated

Students and parents can:
- See what was taught and what homework was assigned
- Access any active homework codes
- No login required to view

Teachers manage their page via WhatsApp commands:
- "Show my page" -- returns the URL
- "Hide lesson from page" -- removes a specific lesson
- "Add class: SS2 Biology" -- organizes lessons by class

#### Parent WhatsApp Updates (V2.1)

Opt-in weekly digest sent to parents via WhatsApp:
- "This week in SS2 Biology: Photosynthesis, Cell Structure. Homework due: Design a poster explaining photosynthesis."
- Simple, non-intrusive. One message per week per subject.

---

## Phase Plan

### V1.0 -- Foundation (DONE)

What was built:
- WhatsApp webhook (Twilio) + web chat UI with Three.js background
- OpenRouter LLM integration (Grok 4.1 Fast via OpenAI SDK)
- PDF download (FPDF2, latin-1 core fonts)
- Supabase session logging
- Basic 3-block lesson pack (Hook, Fact, Application)

---

### V1.1 -- Content Depth (DONE)

Goal: make every lesson pack good enough that a teacher uses it tomorrow without editing.

Changes:
- [x] Redesign system prompt for richer, more practical content
- [x] Restructure to 5 blocks: OPENER, EXPLAIN, ACTIVITY, HOMEWORK, TEACHER_NOTES
- [x] Exercise-book-first homework formats (stories, games, challenges, detective cases)
- [x] Add TEACHER_NOTES block (assessment tips, expected answers, common mistakes)
- [x] Improve ACTIVITY block (timing, grouping, materials, large-class-friendly)
- [x] Curriculum awareness: prompt includes country/exam board context (WAEC, NECO, Cambridge)
- [ ] Test with 5 real teachers -- iterate on content quality based on feedback

Success metric: 3 of 5 teachers say "I would use this tomorrow" without editing.

---

### V1.2 -- Homework Codes (DONE -- 1 item deferred to V2.0)

Goal: bridge the gap between classroom and home for students with phone access.

Changes:
- [x] Generate unique 6-char code per lesson pack
- [x] Build lightweight student page (`/h/CODE`) -- homework instructions + 5-question quiz
- [x] Quiz auto-generated from lesson content by LLM (second LLM call, JSON output)
- [x] Student enters name + class, submits answers (auto-graded, correct/wrong highlighting)
- [ ] Teacher receives results summary via WhatsApp (outbound Twilio not built)
- [x] Results page accessible on web (`/h/{code}/results` with stats, per-question breakdown, submissions table)
- [x] Homework code expiry (14-day TTL -- `_is_expired()` check on retrieval)

Technical (done):
- Supabase tables: `homework_codes`, `quiz_submissions`
- Endpoints: `GET /h/{code}`, `GET /api/h/{code}`, `POST /h/{code}/submit`
- homework.html quiz page (~5KB, works on 2G)

---

### V1.3 -- Stabilisation (DONE)

Goal: fix usability bugs and technical debt that would block real teacher adoption. Every item here was found during code review of V1.0-V1.2 deliverables.

#### Critical (breaks core functionality)

- [x] **WhatsApp session window resets hourly.** Replaced hourly window with phone-number-based persistent session. Teachers can send "new" or "new lesson" to reset.
- [x] **WhatsApp homework URL is a relative path.** Now constructs absolute URL using request scheme + host.
- [x] **WhatsApp message truncation.** Lesson packs over 1500 chars now send a structured summary (block titles + homework code) instead of the full text. Full content is in the attached PDF.
- [x] **Voice note sends placeholder to LLM.** Now rejects voice notes gracefully with a helpful message instead of passing junk to the model.
- [x] **PDF crashes on common Unicode.** Extended latin-1 sanitizer to handle degree, multiplication, division, arrows, naira, pi, square root, comparison operators, and Celsius symbols. Changed `encode('latin-1', 'ignore')` to `'replace'` as final fallback.
- [x] **No Twilio webhook validation.** Added `RequestValidator` signature checking when `TWILIO_AUTH_TOKEN` is set.

#### Important (degrades experience)

- [x] **Web session resets on page refresh.** threadId now persisted in localStorage.
- [x] **Session history too shallow.** Increased default from 3 to 10 messages.
- [x] **Three.js background too heavy for target devices.** Replaced 90-mesh Three.js scene with a CSS animated gradient. Removed Three.js dependency entirely (~200KB saved).
- [x] **PDF has no identifying header.** PDF now shows the teacher's request as a subtitle and the generation date.
- [x] **Clarifying questions ask one field at a time.** System prompt now instructs the model to ask for ALL missing fields in a single message.

#### Cleanup (technical debt)

- [x] Dead code: removed `BLOCK_TYPE_LABELS` from pdf_generator.py, legacy block icons from index.html, unused `get_quiz_results` import
- [x] Orphan files: removed 6 unreferenced images from `static/images/`, removed inert `docker-compose.yml`, removed unused `static/js/three.min.js`
- [x] Created `.dockerignore` excluding `.env`, `.venv/`, tests, generated PDFs, images
- [x] Added `/health` endpoint
- [x] PDF cleanup on startup -- deletes PDFs older than 24 hours via lifespan event
- [x] Replaced `"dummy_key"` fallback with a loud startup warning when `OPENROUTER_API_KEY` is missing
- [x] Fixed redundant `except (json.JSONDecodeError, Exception)` in `_generate_quiz_questions`
- [x] CI pipeline -- GitHub Actions workflow with pytest + ruff lint on push/PR

---

### V2.0 -- Teacher Profiles (DONE)

Goal: give teachers a persistent identity and their students a reference point.

Changes:
- [x] WhatsApp-based teacher registration (phone number = identity, `register [Name]` command)
- [x] Public teacher profile page (`/t/{slug}`) -- Jinja2 template with shared base
- [x] Active homework codes listed on profile (linked to quiz page + results)
- [x] Class organization (`add class: SS2 Biology` command, badge display on profile)
- [x] WhatsApp command router (`commands.py`) -- help, register, my page, add class, results, my codes, new
- [x] Data access layer refactor (`db.py`) -- all Supabase ops with in-memory fallback, separated from LLM client

Technical:
- New Supabase table: `teachers` (phone PK, name, slug, school, classes jsonb)
- `homework_codes` table extended with `teacher_phone` foreign key
- `commands.py` -- command router with `handle_command()` entry point
- `db.py` -- all data operations (sessions, homework, quizzes, teachers)
- `utils.py` -- slimmed to OpenRouter client + homework code generator only
- `templates/base.html` -- shared Jinja2 base template for all lightweight pages
- `templates/profile.html` -- teacher profile page

---

### V2.1 -- Parent & Student Layer (DONE)

Goal: extend the value chain beyond the classroom.

Changes:
- [x] Opt-in parent WhatsApp digest (`subscribe parent [phone] [name] [class]` command, `parent_subscriptions` table, `messaging.py` outbound module)
- [x] Student progress tracking (`progress [Name] [Class]` command, aggregates scores across all quizzes)
- [x] Class leaderboard (`leaderboard CODE` command, ranked by score)
- [x] "Study mode" (`study [topic]` command, sends topic to LLM with recap-focused prompt, returns concise study notes)

---

### V3.0 -- Platform

Goal: ClassGen becomes the tool a school subscribes to, not just individual teachers.

#### 3.0a -- Curriculum Assist & Batch Generation

**The primary flow is always on-demand:** teacher sends any topic, gets a lesson. Curriculum data is an *assist* layer -- it helps teachers who want suggestions, not a rigid sequence they must follow.

Reality: most teachers will not follow a strict curriculum order. They'll teach what they need tomorrow based on where their class is, exam proximity, or what a student struggled with. The system must never assume sequential progression.

- [x] Curriculum data: WAEC SS1-SS3 topic lists for Biology, Mathematics, Chemistry, Physics, English (`curriculum.py`)
- [x] "Suggest" command: `suggest SS2 Biology` → shows uncovered/covered topics. `suggest` with no class lists teacher's classes.
- [x] Topic history: `covered SS2 Biology` → shows what the teacher has already generated. Logged automatically on lesson generation.
- [x] Content cache: deduplicate LLM calls for identical (subject, topic, class, exam_board) tuples across teachers. Cache hit skips LLM.
- [x] Batch generation: `jobs.py` async job queue with Redis support and in-memory fallback, `run_batch_generation()` processes N topics sequentially
- [x] Combined week-pack PDF: `generate_week_pack()` in pdf_generator.py produces multi-lesson documents

Technical:
- New Supabase tables: `curriculum_topics` (exam_board, subject, class, topic), `lesson_history` (teacher_phone, class, topic, created_at)
- `curriculum.py` -- topic lookup, suggestion list, coverage tracking
- Redis job queue for async batch generation (already in docker-compose)
- Combined PDF generator (extend pdf_generator.py for multi-lesson packs)

Note: timetable upload (scheduling *when* classes happen) is a school-admin concern for V3.0c, not needed here.

#### 3.0b -- Billing & Subscriptions (DONE)

- [x] Payment abstraction layer (`billing.py`) -- provider-agnostic with `PaymentProvider` base class
- [x] Paystack provider: `PaystackProvider` with payment link creation and verification
- [x] Bank transfer provider: `BankTransferProvider` with instructions and reference codes
- [x] Subscription tiers: Free (5 lessons/week), Premium (unlimited, NGN 2,000/mo), School (per-seat, NGN 5,000/mo)
- [x] Usage tracking: `log_usage()` on each lesson, `check_usage()` before LLM calls with friendly limit message
- [x] Usage quota enforced in webhook handler -- blocked teachers see upgrade message

Technical:
- New Supabase tables: `subscriptions`, `usage_log`
- `billing.py` -- tiers, usage tracking, subscription management, payment providers
- Usage middleware integrated into webhook handler

#### 3.0c -- School Admin & Worksheets (DONE)

- [x] School admin dashboard at `/s/{slug}` -- teacher count, lesson count, teacher table with profile links
- [x] Printable worksheet generator (`worksheet.py`) -- bingo grids, fill-in-the-blank, flashcard cut-outs
- [ ] Theme customization: school logo/name on PDFs and profile pages (deferred)
- [ ] File storage migration: move to Supabase Storage or S3 (deferred -- local static/ sufficient for current scale)
- [ ] Data export: CSV/PDF export (deferred)

Technical:
- `worksheet.py` -- `generate_bingo_grid()`, `generate_fill_in_blank()`, `generate_flashcards()`
- `templates/admin.html` -- school admin dashboard extending base template
- `db.py` -- school CRUD operations

#### 3.0d -- Multi-language (DONE)

- [x] Multi-language support via system prompt -- responds in the teacher's language automatically
- [x] Bilingual lesson packs supported -- teacher requests "in English and Yoruba" and gets both

---

### V3.1 -- Web Teacher Profiles & Settings (DONE)

Goal: bring the teacher identity model (previously WhatsApp-only) to the web chat UI.

Changes:
- [x] Web teacher registration via sidebar (threadId = identity, reuses `teachers` table)
- [x] Profile sidebar panel: editable name, stats (total/this week/this month), class badges, recent homework codes
- [x] Settings panel: push notification toggle, clear chat history
- [x] `/api/chat` now links homework codes to registered web teachers (enables stats tracking)
- [x] REST endpoints: `GET/POST/PATCH /api/teacher/profile`, `POST/DELETE /api/teacher/classes`, `DELETE /api/teacher/history`
- [x] Test coverage for all new endpoints (9 tests)

Technical:
- threadId serves as the `phone` field in the `teachers` table -- no schema changes needed
- `db.py` -- added `remove_teacher_class()`, `update_teacher_name()`, `clear_session_history()`
- Sidebar uses same glassmorphism styling as the chat UI

### V3.2 -- Deferred Items (DONE)

Goal: wire up deferred features from earlier phases and add teacher engagement tools.

Changes:
- [x] WhatsApp quiz result notifications to teachers (V1.2 deferred) -- milestone-based throttling (1st, 5th, 10th, then every 10th submission)
- [x] School admin quiz submission count (was hardcoded 0)
- [x] CSV data export: `GET /t/{slug}/export` (teacher) and `GET /s/{slug}/export` (school)
- [x] Teacher lesson stats: `stats` WhatsApp command + stats card on profile page
- [x] Quiz submission log: `log CODE` WhatsApp command (first finisher, top scorer, chronological order)
- [x] School branding on PDFs (opt-in only -- teacher is the SI-unit, not the school)

---

## Shared Technical Modules

These modules cut across multiple phases. Building them right avoids rewriting later.

### Built (V2.0)

| Module | Purpose | Status |
|---|---|---|
| `commands.py` | WhatsApp command router -- matches text, falls through to LLM | DONE. 14 commands: help, register, my page, add class, my codes, results, log, leaderboard, progress, subscribe parent, stats, study, new, reset |
| `db.py` | Data access layer -- Supabase + in-memory fallback, `save/get/list` patterns | DONE. Tables: sessions, teachers, homework_codes, quiz_submissions, parent_subscriptions |
| `utils.py` | OpenRouter LLM client + homework code generator (slimmed from original) | DONE |
| `templates/` | Jinja2 shared base template + page templates | DONE. base.html, profile.html |
| `messaging.py` | Outbound Twilio WhatsApp messaging (proactive messages) | DONE. send_whatsapp, send_quiz_summary, send_parent_digest |

### Needed for V3.0

| Module | Purpose | Phase |
|---|---|---|
| `billing.py` | Payment abstraction -- provider-agnostic layer over Paystack (card/USSD) and bank transfer | 3.0b |
| `curriculum.py` | Curriculum topic lists -- (exam_board, subject, class) → topic suggestions, coverage tracking (assist, not enforcement) | 3.0a |
| `jobs.py` | Async job queue via Redis -- batch lesson generation, weekly parent digests | 3.0a |
| `worksheet.py` | Layout-aware PDF generator -- game grids, fill-in-blanks, cut-out cards (separate from lesson PDFs) | 3.0c |
| `storage.py` | File storage abstraction -- local static/ for dev, Supabase Storage/S3 for production | 3.0c |

---

## What We Are NOT Building (Yet)

| Idea | Why not now |
|---|---|
| Student mobile app | Exercise book is the platform. Web page with homework code is enough. |
| LMS / Moodle competitor | We generate content and measure engagement. We don't manage courses, schedules, or grades. |
| AI tutor for students | Teacher is the delivery mechanism. Student-facing AI dilutes the teacher's role. |
| Video content | Bandwidth constraints. Text + teacher performance + multi-sensory activities > video. |
| Real-time collaborative editing | Teachers remix asynchronously. Real-time collab is a different product. |
| Blockchain/crypto tokens | The trust model uses blockchain principles, not blockchain technology. |
| Complex gamification | The game IS the homework format (adventures, detective cases), not a separate points/badges system. |

---

## V4 — Structured Output, Adaptive Rendering & Education Intelligence

See [DESIGN-v4-structured-output.md](DESIGN-v4-structured-output.md) for the full design spec.

### Content Philosophy (updated)

1. **Paper-first.** Every lesson pack must work perfectly when read aloud or written on a chalkboard. Technology is an enhancement layer, never a requirement.
2. **Teacher as performer.** The teacher is the delivery mechanism. Our content gives them material to *perform* -- hooks, stories, challenges, surprises -- not walls of text to dictate.
3. **Exercise book is the student's platform.** For most students, their exercise book is the only tool they take home. Homework must be designed to be completed in an exercise book with nothing else.
4. **Classroom is the environment.** Physical activities, group dynamics, movement, debate, presentation -- the classroom is a multi-sensory learning space, not rows of silent desks.
5. **Teacher is the trust anchor.** Chosen by parents, endorsed by education bodies, certified by institutions. The platform's quality, safety, and governance flow through the teacher network.

---

### V4.0 — Project Restructure (DONE)

**Goal:** Reorganize from flat-file layout to proper `src/classgen/` package with layered architecture. Foundation for all V4 features.

#### Target Layout

```
src/classgen/
  core/           # Domain models (Pydantic). No I/O, no framework deps.
    lesson.py       LessonPack, OpenerBlock, ExplainBlock, ActivityBlock, HomeworkBlock, TeacherNotesBlock
    quiz.py         QuizQuestion, GradedResult
    homework.py     HomeworkTask, AdventureType enum, ExerciseBookFormat enum
    teacher.py      Teacher, TrustLevel enum, VerificationStatus
    student.py      StudentIdentity (5-layer progressive model)
    billing.py      SubscriptionTier, UsageCheck, TIER_PRICES

  data/            # Persistence. Supabase/PostgREST + in-memory fallback.
    client.py       Supabase client init (PostgREST URL fix)
    sessions.py     log_session, get_session_history, clear
    teachers.py     save/get/update teacher, slug generation, class lists
    homework.py     save/get/list homework codes, TTL expiry
    quiz.py         save/get quiz submissions, leaderboard, progress
    lessons.py      log_generated, covered topics, cache operations
    subscriptions.py  get/save subscription, log/get usage
    schools.py      save/get school, get school teachers
    parents.py      save/list/unsubscribe parent subscriptions
    push.py         save/get/remove push subscriptions
    threads.py      active thread mapping (in-memory only)

  services/        # Business logic. Orchestrates data + LLM.
    llm.py          OpenRouter client, call_openrouter(), streaming variant
    lesson_service.py   generate_lesson(), finalize(), cache logic
    quiz_service.py     generate_quiz_questions(), grade_submission()
    homework_service.py generate_homework_code(), adventure logic
    batch_service.py    run_batch_generation()
    billing_service.py  check_usage(), payment providers
    notification_service.py  send_push(), notify_quiz_submission()

  channels/        # Rendering. Transforms LessonPack → channel-specific output.
    base.py         ChannelAdapter ABC, render() interface
    web.py          Rich HTML cards, SSE block streaming
    whatsapp.py     Plain text dictation format
    pdf.py          Wraps pdf_generator for structured input
    sms.py          Minimal text for feature phones
    registry.py     get_adapter(channel) factory

  content/         # Static content + document generators.
    curriculum.py   TOPICS dict, suggest/covered logic
    pdf_generator.py  ClassGenPDF, generate_pdf_from_markdown
    worksheet.py    Bingo grids, fill-in-blank, flashcards
    prompts.py      CLASSGEN_SYSTEM_PROMPT, QUIZ_GENERATION_PROMPT, BLOCK_PATTERN

  integrations/    # Third-party clients.
    twilio.py       send_whatsapp(), send_quiz_summary(), send_parent_digest()
    redis_queue.py  Redis/in-memory job queue

  commands/        # WhatsApp/web command router.
    router.py       handle_command() dispatch
    handlers.py     All _cmd_* implementations

  api/             # FastAPI routers. Thin — no business logic.
    app.py          App factory, lifespan, static mount, health check
    schemas.py      All Pydantic request/response models
    chat.py         POST /api/chat, GET /api/chat/stream (SSE)
    webhook.py      POST /webhook/twilio
    homework.py     GET /h/{code}, POST /h/{code}/submit
    teacher.py      Teacher profile API endpoints
    school.py       School admin dashboard + export
    profile.py      Public teacher profile pages
    push.py         Push subscription endpoints
    dev.py          Dev seed endpoint

  i18n.py          Locale/currency formatting (top-level, no sub-package)

scratch/           # Experiments — NOT importable, NOT in package.
  prompts/           LLM prompt experiments, JSON schema drafts
  sql/               Data exploration queries
  ui/                HTML/CSS prototypes, component mockups
  scripts/           Integration test scripts, one-off tools
  perf/              Load testing, stack validation
```

**Dependency direction:** `core` ← `data` ← `services` ← `api`. `channels` imports `core` only. No circular imports.

#### User Stories

**US-4.0.1: Package restructure**
- As a developer, when I run `uv run pytest`, all existing tests pass against the new `src/classgen/` layout.
- Architecture: Update `pyproject.toml` (`packages = ["src"]`, ruff `src = ["src"]`). Root `main.py` becomes a one-liner (`from classgen.api.app import app`). Dockerfile CMD unchanged.
- Tables: None (no schema changes)
- Modules: All current modules → new locations per migration map
- Endpoints: All existing endpoints preserved, same paths

**US-4.0.2: Scratchpad directories**
- As a developer, I have gitignored scratch directories for prompt experiments, SQL exploration, UI prototypes, test scripts, and performance testing.
- Architecture: `scratch/` with 5 subdirectories, each with `README.md`. Added to `.gitignore` for `scratch/scripts/` and `scratch/perf/` (may contain credentials). `scratch/prompts/` and `scratch/sql/` are committed.

---

### V4.1 — Structured Output + Channel Adapters (DONE)

**Goal:** LLM returns structured JSON instead of text blocks. Each channel renders the same data differently. SSE streaming eliminates the dead wait on web.

**Status:** Implemented and deployed (April 2026). All features flag-gated behind `FF_STRUCTURED_OUTPUT`, `FF_SSE_STREAMING`, `FF_JSON_RESPONSE_FORMAT`, `FF_EMBEDDED_QUIZ`. Flags default off; production flags off. Additionally: 3-slide web onboarding intro, WhatsApp welcome with terms acceptance, `/terms` page, conversation persistence, toast/native notifications, DM Serif Display headings in overlays. 350 tests.

#### User Stories

**US-4.1.1: Structured LLM output**
- As a teacher, when I request a lesson, the system returns a structured JSON lesson pack with typed blocks (opener, explain, activity, homework, teacher_notes), each with rich metadata (format, duration, materials, key terms, quiz embedded in homework).
- Architecture:
  - Model: `src/classgen/core/lesson.py` → `LessonPack` Pydantic model with discriminated union blocks
  - Prompt: `src/classgen/content/prompts.py` → updated system prompt requesting JSON output
  - LLM: `src/classgen/services/llm.py` → `call_openrouter()` gains `response_format={"type": "json_object"}`
  - Validation: `LessonPack.model_validate_json(response)` with fallback to raw text
  - Storage: `lesson_cache.content` stores JSON string. `homework_codes.lesson_content` stores JSON string. New migration adds `lesson_json jsonb` column or replaces text column.
  - Eliminates: `_has_lesson_blocks()`, `_extract_homework_block()`, `_clean_block_markers_for_pdf()`, `_generate_quiz_questions()` (quiz now embedded in homework block), 4 regex patterns across 3 files

**US-4.1.2: Web adapter — rich lesson cards**
- As a teacher using the web chat, when a lesson pack arrives, I see a compact lesson card with the opener quote, block icons (Teach / Play / Homework), and action buttons (PDF, homework code). Tapping a block opens an instant-view overlay with rich formatting (headings, key terms, equations).
- Architecture:
  - Adapter: `src/classgen/channels/web.py` → `WebAdapter.render(lesson_pack) -> dict` (HTML fragments per block)
  - Frontend: `index.html` → new `renderLessonCard()` function replacing `renderBlock()` regex parsing
  - Endpoint: `POST /api/chat` response gains `blocks: list[dict]` alongside `reply`

**US-4.1.3: WhatsApp adapter — dictation format**
- As a teacher using WhatsApp, when a lesson is generated, I receive a concise summary with block titles, the opener quote, activity format, and homework code link — formatted for reading aloud.
- Architecture:
  - Adapter: `src/classgen/channels/whatsapp.py` → `WhatsAppAdapter.render(lesson_pack) -> str`
  - Replaces: `_whatsapp_summary()` regex function in current `main.py`

**US-4.1.4: PDF adapter**
- As a teacher, when I download a lesson PDF, the document renders each block with proper headings, page breaks, and the homework adventure narrative formatted for printing.
- Architecture:
  - Adapter: `src/classgen/channels/pdf.py` → `PdfAdapter.render(lesson_pack) -> str` (file path)
  - Wraps: `src/classgen/content/pdf_generator.py` with structured input instead of regex-parsed text
  - Eliminates: `block_pattern` regex in `pdf_generator.py`

**US-4.1.5: SSE streaming**
- As a teacher using the web chat, I see the lesson build block-by-block in ~2 seconds per block instead of waiting 10-20 seconds for the full response.
- Architecture:
  - Endpoint: `GET /api/chat/stream` → `StreamingResponse` with `text/event-stream`
  - Service: `src/classgen/services/llm.py` → streaming variant using OpenRouter streaming API
  - Frontend: `index.html` → `EventSource` listener, renders each SSE block event as it arrives
  - WhatsApp: unaffected (waits for full response)

---

### V4.2 — Adventure Homework

**Goal:** Homework evolves from 5 MCQ questions to narrative adventures with real-world tasks, exercise-book formats, and embedded quizzes.

#### User Stories

**US-4.2.1: Homework as narrative adventure**
- As a teacher, when a lesson is generated, the homework block contains a story-embedded adventure where the student is the main character. Tasks combine real-world observation, calculation, comprehension, and creativity — each producing something written in the exercise book.
- Architecture:
  - Model: `src/classgen/core/homework.py` → `HomeworkTask(id, instruction, type, clue, exercise_book_format)`, `AdventureType` enum (detective, expedition, design_challenge, story_mission, relay_puzzle, community_interview)
  - Prompt: Updated system prompt in `prompts.py` with adventure format examples
  - Schema: `homework_codes` table → `lesson_json jsonb` replaces or supplements `lesson_content text`

**US-4.2.2: Adventure homework page**
- As a student visiting `/h/CODE`, I see the adventure narrative, each task with its exercise-book format guidance, and the supplementary quiz — not just 5 bare MCQ questions.
- Architecture:
  - Frontend: `homework.html` redesigned → narrative header, task cards with format icons, quiz section
  - Endpoint: `GET /api/h/{code}` returns structured homework data from JSON lesson pack

**US-4.2.3: Teacher feasibility review**
- As a teacher, before assigning a homework adventure, I can see safety notes and feasibility flags (e.g., "This activity requires visiting a river"). I can approve or request a regeneration.
- Architecture:
  - Model: `teacher_notes.safety_notes` field in `TeacherNotesBlock`
  - Endpoint: `POST /api/homework/{code}/approve` (teacher confirms feasibility)
  - Web UI: approval toggle on the homework instant view

---

### V4.3 — Student Identity + Community

**Goal:** Students gain progressive identity (teacher-scoped first). Teachers can publish lessons to the community. Peer rating begins.

#### User Stories

**US-4.3.1: Progressive student identity (Layer 1)**
- As a teacher, when my student submits a quiz as "Amina, SS2A", I can see Amina's scores across all my homework codes — without Amina creating an account.
- Architecture:
  - Model: `src/classgen/core/student.py` → `StudentIdentity(name, class_name, teacher_phone)` with collision detection
  - Table: New `students` table: `id, name, class_name, teacher_phone, parent_phone_last4 nullable, created_at`
  - Migration: `003_add_students.sql` — create table, update `quiz_submissions` to reference `student_id`
  - Endpoint: `GET /api/teacher/{phone}/students` — list students with cross-homework scores

**US-4.3.2: Student progress view**
- As a student (or parent), when I visit my progress page, I see my scores across subjects, my adventure completion history, and which topics I struggled with.
- Architecture:
  - Endpoint: `GET /api/student/{id}/progress` — aggregated scores by subject
  - Frontend: New `progress.html` page

**US-4.3.3: Teacher publishes lesson to community**
- As a teacher, I can mark a lesson as "shared" so other teachers can discover and use it. My name, school, and subject are shown. I retain ownership.
- Architecture:
  - Table: `community_lessons` → `id, homework_code, teacher_phone, subject, class_level, shared_at, rating_avg, use_count`
  - Endpoint: `POST /api/lesson/{code}/share`
  - Data: `src/classgen/data/community.py` — new module

**US-4.3.4: Peer rating and discovery**
- As a teacher, I can browse community lessons by subject and class, see ratings and use counts, and use a shared lesson with my class (creating my own homework code from the shared content).
- Architecture:
  - Endpoint: `GET /api/community/lessons?subject=Biology&class=SS2` — paginated, sorted by rating
  - Endpoint: `POST /api/community/lessons/{id}/rate` — 1-5 star rating
  - Endpoint: `POST /api/community/lessons/{id}/use` — fork lesson, create new homework code

---

### V4.4 — Teacher Trust Network + Analytics

**Goal:** Teachers earn trust through verified credentials and engagement. Content is co-moderated. Analytics flow from teacher to ministry.

#### User Stories

**US-4.4.1: Teacher verification**
- As a teacher, I can add my certification number, school affiliation, and teaching experience to my profile. School admin confirms the affiliation. Verified teachers get a badge and their shared content is prioritized.
- Architecture:
  - Model: `src/classgen/core/teacher.py` → `TrustLevel` enum (teacher, verified, subject_lead, school_admin, reviewer)
  - Table: `teacher_verification` → `teacher_phone, certification_number, school_slug, years_experience, verified_at, verified_by`
  - Migration: `004_add_verification.sql`
  - Endpoint: `POST /api/teacher/verify`, `POST /api/school/{slug}/confirm-teacher`

**US-4.4.2: Content flagging and peer review**
- As a verified teacher, I can flag a community lesson for inaccuracy, safety concern, or inappropriate content. Flags are reviewed by subject leads (peer teachers with high trust scores), not a central team.
- Architecture:
  - Table: `content_flags` → `id, lesson_id, flagged_by, reason, status (open/confirmed/dismissed), reviewed_by`
  - Endpoint: `POST /api/community/lessons/{id}/flag`, `POST /api/community/flags/{id}/review`

**US-4.4.3: Community-verified content**
- As a teacher browsing community lessons, I can see which lessons are "community verified" — endorsed by multiple certified teachers across different schools.
- Architecture:
  - Table: `lesson_endorsements` → `lesson_id, teacher_phone, endorsed_at`
  - Logic: Lesson becomes "verified" when endorsed by N verified teachers from M different schools
  - Endpoint: `POST /api/community/lessons/{id}/endorse`

**US-4.4.4: Lesson remix**
- As a teacher, I can fork a community-verified lesson, adapt blocks for my context (different opener, localized activity), and publish the remix. The original is credited.
- Architecture:
  - Table: `community_lessons.forked_from` — nullable reference to parent lesson
  - Endpoint: `POST /api/community/lessons/{id}/remix` → creates new lesson with modified blocks
  - Model: `LessonPack` supports block-level replacement

**US-4.4.5: Teacher analytics dashboard**
- As a teacher, I see a dashboard with: lessons generated this week/month, student engagement (quiz scores, adventure completion), my hardest topics (where students score lowest), and peer comparison (how my engagement compares to subject average).
- Architecture:
  - Endpoint: `GET /api/teacher/{phone}/analytics` — aggregated metrics
  - Data: Computed from `homework_codes`, `quiz_submissions`, `lesson_history`, `community_lessons`

**US-4.4.6: School admin analytics**
- As a school admin, I see: which teachers are active, subject coverage gaps (topics not taught with N weeks left in term), student performance trends, and homework completion rates.
- Architecture:
  - Endpoint: `GET /api/school/{slug}/analytics` — anonymized student data, teacher activity
  - Data: Aggregated from teacher-scoped data within the school

**US-4.4.7: Anonymized regional analytics**
- As a ministry/curriculum body, I see anonymized aggregate data: topic difficulty nationwide (which topics have lowest scores), format effectiveness (adventure vs quiz-only completion rates), regional patterns, and novel teaching approaches emerging from the community.
- Architecture:
  - Endpoint: `GET /api/analytics/regional?country=NG&region=Lagos` — no student PII, no teacher names
  - Data: Aggregated from `lesson_history`, `quiz_submissions`, `community_lessons`, grouped by region/subject/class
  - Model: Teacher is the anchor entity — `Teacher 454F32 teaches 2 subjects, 55 students, avg 72%`

---

## Architecture Traceability Matrix

Every user story traces to: schema changes → new/modified modules → endpoints.

| Story | Tables | Modules | Endpoints |
|---|---|---|---|
| US-4.0.1 | None | All (restructure) | All (preserved) |
| US-4.1.1 | `lesson_cache` (json), `homework_codes` (json) | `core/lesson.py`, `content/prompts.py`, `services/llm.py`, `services/lesson_service.py` | `POST /api/chat` |
| US-4.1.2 | None | `channels/web.py`, `index.html` | `POST /api/chat` (response format) |
| US-4.1.3 | None | `channels/whatsapp.py` | `POST /webhook/twilio` |
| US-4.1.4 | None | `channels/pdf.py`, `content/pdf_generator.py` | PDF download URL |
| US-4.1.5 | None | `services/llm.py`, `api/chat.py`, `index.html` | `GET /api/chat/stream` |
| US-4.2.1 | `homework_codes` (json) | `core/homework.py`, `content/prompts.py` | `POST /api/chat` |
| US-4.2.2 | None | `homework.html` | `GET /api/h/{code}` |
| US-4.2.3 | None | `core/lesson.py` (safety_notes) | `POST /api/homework/{code}/approve` |
| US-4.3.1 | `students` (new) | `core/student.py`, `data/students.py` | `GET /api/teacher/{phone}/students` |
| US-4.3.2 | None | `progress.html` | `GET /api/student/{id}/progress` |
| US-4.3.3 | `community_lessons` (new) | `data/community.py` | `POST /api/lesson/{code}/share` |
| US-4.3.4 | `community_lessons` | `data/community.py` | `GET /api/community/lessons`, rate, use |
| US-4.4.1 | `teacher_verification` (new) | `core/teacher.py`, `data/teachers.py` | `POST /api/teacher/verify` |
| US-4.4.2 | `content_flags` (new) | `data/community.py` | `POST /api/.../flag`, `.../review` |
| US-4.4.3 | `lesson_endorsements` (new) | `data/community.py` | `POST /api/.../endorse` |
| US-4.4.4 | `community_lessons.forked_from` | `data/community.py` | `POST /api/.../remix` |
| US-4.4.5 | None (reads existing) | `services/analytics.py` | `GET /api/teacher/{phone}/analytics` |
| US-4.4.6 | None (reads existing) | `services/analytics.py` | `GET /api/school/{slug}/analytics` |
| US-4.4.7 | None (reads existing) | `services/analytics.py` | `GET /api/analytics/regional` |

## Migration Sequence

| # | File | Phase | Description |
|---|---|---|---|
| 001 | `001_baseline.sql` | V3.1 | Marker for init.sql schema (applied) |
| 002 | `002_add_updated_at.sql` | V3.1 | updated_at columns + triggers (applied) |
| 003 | `003_lesson_json.sql` | V4.1 | Add `lesson_json jsonb` to `homework_codes` and `lesson_cache`. Backfill from text columns. |
| 004 | `004_add_students.sql` | V4.3 | Create `students` table. Add `student_id` to `quiz_submissions`. |
| 005 | `005_add_community.sql` | V4.3 | Create `community_lessons`, indexes on subject/class/rating. |
| 006 | `006_add_verification.sql` | V4.4 | Create `teacher_verification`, `content_flags`, `lesson_endorsements`. |

---

## Implementation Order

```
V4.0  Restructure to src/classgen/         ✅ DONE (April 2026)
  ↓
V4.1  Structured output + adapters + SSE   ✅ DONE (April 2026, flag-gated)
  ↓
V4.2  Adventure homework                   ← NEXT: content quality leap
  ↓
V4.3  Student identity + community         ← network effects begin
  ↓
V4.4  Trust network + analytics            ← platform intelligence
```

Each phase is independently deployable. V4.2 onward adds new capabilities.
