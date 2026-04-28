# ClassGen Product Roadmap

Confidential -- Working Draft | March 2026 (reviewed April 2026)

> **April 2026 review note.** V4.1 shipped broader than originally scoped — billing enforcement, web push, and most of V4.2's data model all landed flag-gated. V4.2 is re-scoped: the student-facing UI consuming `homework_structured` is the remaining gap (see V4.2a below). Before starting V4.2a, validate V4.1 with flags on via `.mock/e2e/` parity and consider enabling `FF_STRUCTURED_OUTPUT` in production so the data V4.2a renders actually flows.

**Status convention:** `[x]` shipped to codebase · `[ ]` planned · `[~]` partial / scaffold only. Deployment and feature-flag state is documented per phase — e.g. V4.1 features are merged but flag-gated off in production as of April 2026. Every user story and bullet in this doc uses these markers so status is readable at a glance.

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
- [x] WhatsApp webhook (Twilio) + web chat UI with Three.js background
- [x] OpenRouter LLM integration (Grok 4.1 Fast via OpenAI SDK)
- [x] PDF download (FPDF2, latin-1 core fonts)
- [x] Supabase session logging
- [x] Basic 3-block lesson pack (Hook, Fact, Application)

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
- [x] Test with 5 real teachers -- iterate on content quality based on feedback (April 2026, via web emulator; teachers confirmed features satisfied their immediate needs)

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
- [~] Batch generation: Redis queue scaffold lives in `src/classgen/integrations/redis_queue.py` (in-memory fallback). No `run_batch_generation()` service or WhatsApp-facing batch command currently ships — deferred.
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
- [x] **Country at registration (April 2026)** — registration form captures name + country together, mirroring the public profile's `name · country` subtitle (`templates/profile.html`). Country is required; uses the same region-grouped dropdown as the profile sidebar. First lesson now generates with country context instead of waiting for the teacher to discover the sidebar field. `TeacherRegisterRequest.country` is API-optional but UI-required (WhatsApp registrants get country auto-detected from phone, so the API stays tolerant).
- [x] **Country dropdown polish (April 2026)** — flag emoji per supported country, native `<optgroup>` grouping by region (East Africa → West Africa → Southern Africa → Other; alphabetical within each), 14-market English-speaking scope. Backed by `supported_countries` reference table (migration 006) with in-memory fallback that mirrors the Python constants (`COUNTRY_REGIONS`, `COUNTRY_FLAGS`); test pins phone-auto-detect ⊆ dropdown invariant.
- [x] **Onboarding polish + profile preview slide (April 2026)** — first-visit web intro grew from 3 slides to 4. New slide 3 shows a centered "profile content preview" card (name, country, stats, class badges, sample homework codes) so teachers see what the dashboard looks like populated. Marquee on slide 2 readability bumped (font 0.88rem · weight 600 · 28s animation · pause-on-hover · `prefers-reduced-motion`). Bottom-nav spacing fixed (gap 18px + safe-area-inset). Mobile Chrome scrollbar jiggle fixed via `100dvh` on the overlay. JS extracts `LAST_SLIDE` constant to replace four magic-2s. Marquee examples gain country flag emojis (`🇳🇬 · SS2, Nigeria, …`) so teachers see "we know your country" before registering.
- [x] **Reset-intro setting (April 2026)** — Settings → Intro section adds a "Reset intro" button + "Show intro on next refresh." helper. Clears `localStorage.classgen_intro_seen` and confirms via toast; intro re-shows on the next page load. Lets a teacher demo onboarding to a colleague without clearing browser cache.

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
| Non-English UI / French/Portuguese/Arabic markets | Roadmapped to V5 (see below). The current 14-country English-speaking scope is deliberate — adding French markets without a French interface would ship a half-translated experience. |
| LLM lesson generation in non-English languages | Roadmapped to V6. V5 ships interface translation only; lesson content generation in non-English languages needs separate prompt + evaluation infrastructure. |

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

**[x] US-4.0.1: Package restructure**
- As a developer, when I run `uv run pytest`, all existing tests pass against the new `src/classgen/` layout.
- Architecture: Update `pyproject.toml` (`packages = ["src"]`, ruff `src = ["src"]`). Root `main.py` becomes a one-liner (`from classgen.api.app import app`). Dockerfile CMD unchanged.
- Tables: None (no schema changes)
- Modules: All current modules → new locations per migration map
- Endpoints: All existing endpoints preserved, same paths

**[x] US-4.0.2: Scratchpad directories**
- As a developer, I have gitignored scratch directories for prompt experiments, SQL exploration, UI prototypes, test scripts, and performance testing.
- Architecture: `scratch/` with 5 subdirectories, each with `README.md`. Added to `.gitignore` for `scratch/scripts/` and `scratch/perf/` (may contain credentials). `scratch/prompts/` and `scratch/sql/` are committed.

---

### V4.1 — Structured Output + Channel Adapters (DONE)

**Goal:** LLM returns structured JSON instead of text blocks. Each channel renders the same data differently. SSE streaming eliminates the dead wait on web.

**Status:** Implemented and deployed (April 2026). All features flag-gated behind `FF_STRUCTURED_OUTPUT`, `FF_SSE_STREAMING`, `FF_JSON_RESPONSE_FORMAT`, `FF_EMBEDDED_QUIZ`. Flags default off; production flags off. Additionally: 4-slide web onboarding intro (Welcome → How → Profile preview → Accept), WhatsApp welcome with terms acceptance, `/terms` page, conversation persistence, toast/native notifications, DM Serif Display headings in overlays, WhatsApp flow engine (Redis-backed multi-turn lesson browsing). **Teacher country (April 2026):** migration 005 adds `country` on `teachers`; migration 006 adds `supported_countries` reference table seeded with 14 English-speaking markets grouped by region. Country auto-detected from WhatsApp phone prefix on `YES` onboarding (via `country_from_phone()` in `i18n.py`), required at web registration via region-grouped dropdown with flag emojis; injected into LLM prompt via shared `_country_context()` helper (covers blocking `/api/chat` and SSE `/api/chat/stream`). 461 tests, ruff clean.

**Also live (under-credited in earlier phase entries):**
- **Billing enforcement is wired, not just scaffolded.** `check_usage()` gates `/api/chat` (`api/chat.py:329,462`) and `/webhook/twilio` (`api/webhook.py:149`); `log_usage()` records on success. Free-tier quota actively blocks over-limit teachers with an upgrade message. Paystack and bank-transfer providers exist in `core/billing.py`, `services/billing_service.py`.
- **Web push notifications.** `GET /api/vapid-key` + `POST /api/push/subscribe` (`api/push.py`), `notify_quiz_submission()` invoked from the homework submit path (`api/homework.py:129`). Teacher receives browser notifications when students submit.
- **Teacher lesson stats.** `get_teacher_lesson_stats()` powers the profile-page stats card and the WhatsApp `stats` command.
- **Empty-content recovery (April 2026).** When the LLM emits a clean `Title:/Summary:/Details:` lesson but drops the `[BLOCK_START_X]/[BLOCK_END]` outer markers (1/5 occurrence in flags-off perf bench 2026-04-28), `parse_lesson_response()` falls back to a positional recovery parser that maps the sections to opener/explain/activity/homework/teacher_notes. PDF + homework code now generate correctly instead of silently dropping; recovery frequency is observable via `[recovery] no-markers fallback fired blocks=N` log lines. Covered by `tests/test_parsers.py::TestNoMarkersRecovery` (8 unit tests) and `tests/test_main.py::test_chat_recovers_lesson_when_llm_omits_block_markers` (integration).

#### User Stories

**[x] US-4.1.1: Structured LLM output**
- As a teacher, when I request a lesson, the system returns a structured JSON lesson pack with typed blocks (opener, explain, activity, homework, teacher_notes), each with rich metadata (format, duration, materials, key terms, quiz embedded in homework).
- Architecture:
  - Model: `src/classgen/core/lesson.py` → `LessonPack` Pydantic model with discriminated union blocks
  - Prompt: `src/classgen/content/prompts.py` → updated system prompt requesting JSON output
  - LLM: `src/classgen/services/llm.py` → `call_openrouter()` gains `response_format={"type": "json_object"}`
  - Validation: `LessonPack.model_validate_json(response)` with fallback to raw text
  - Storage: `lesson_cache.content` stores JSON string. `homework_codes.lesson_content` stores JSON string. New migration adds `lesson_json jsonb` column or replaces text column.
  - Eliminates: `_has_lesson_blocks()`, `_extract_homework_block()`, `_clean_block_markers_for_pdf()`, `_generate_quiz_questions()` (quiz now embedded in homework block), 4 regex patterns across 3 files

**[x] US-4.1.2: Web adapter — rich lesson cards**
- As a teacher using the web chat, when a lesson pack arrives, I see a compact lesson card with the opener quote, block icons (Teach / Play / Homework), and action buttons (PDF, homework code). Tapping a block opens an instant-view overlay with rich formatting (headings, key terms, equations).
- Architecture:
  - Adapter: `src/classgen/channels/web.py` → `WebAdapter.render(lesson_pack) -> dict` (HTML fragments per block)
  - Frontend: `index.html` → new `renderLessonCard()` function replacing `renderBlock()` regex parsing
  - Endpoint: `POST /api/chat` response gains `blocks: list[dict]` alongside `reply`

**[x] US-4.1.3: WhatsApp adapter — dictation format**
- As a teacher using WhatsApp, when a lesson is generated, I receive a concise summary with block titles, the opener quote, activity format, and homework code link — formatted for reading aloud.
- Architecture:
  - Adapter: `src/classgen/channels/whatsapp.py` → `WhatsAppAdapter.render(lesson_pack) -> str`
  - Replaces: `_whatsapp_summary()` regex function in current `main.py`

**[x] US-4.1.4: PDF adapter**
- As a teacher, when I download a lesson PDF, the document renders each block with proper headings, page breaks, and the homework adventure narrative formatted for printing.
- Architecture:
  - Adapter: `src/classgen/channels/pdf.py` → `PdfAdapter.render(lesson_pack) -> str` (file path)
  - Wraps: `src/classgen/content/pdf_generator.py` with structured input instead of regex-parsed text
  - Eliminates: `block_pattern` regex in `pdf_generator.py`

**[x] US-4.1.5: SSE streaming**
- As a teacher using the web chat, I see the lesson build block-by-block in ~2 seconds per block instead of waiting 10-20 seconds for the full response.
- Architecture:
  - Endpoint: `GET /api/chat/stream` → `StreamingResponse` with `text/event-stream`
  - Service: `src/classgen/services/llm.py` → streaming variant using OpenRouter streaming API
  - Frontend: `index.html` → `EventSource` listener, renders each SSE block event as it arrives
  - WhatsApp: unaffected (waits for full response)

---

### V4.2 — Adventure Homework

**Goal:** Homework evolves from 5 MCQ questions to narrative adventures with real-world tasks, exercise-book formats, and embedded quizzes.

**Reality check (April 2026 review):** Most of V4.2 landed quietly under the V4.1 `FF_STRUCTURED_OUTPUT` flag. Server-side: `HomeworkBlock` already carries `narrative`, `tasks`, `format`, `completion`, and embedded `quiz` (`core/models.py:75–85`); `HomeworkTask` has `id/instruction/type/clue/exercise_book_format` (`31–37`); the JSON prompt instructs the LLM to emit them (`content/prompts.py:193–213`); `GET /api/h/{code}` already returns a `homework_structured` payload when `lesson_json` is present (`api/homework.py:62–80`); `TeacherNotesBlock.safety_notes` exists (`models.py:96`). **What's missing is the student-facing UI that consumes this data**, plus the teacher approval endpoint and resolving a format-list mismatch (see US-4.2.1 below).

Re-scoped to two phases:

#### V4.2a — Adventure UI (priority; unblocks existing data)

**[ ] US-4.2.2-rev: Adventure homework page consumes `homework_structured`**
- As a student visiting `/h/CODE`, when the lesson was generated with structured output on, I see the adventure narrative, task cards with exercise-book format hints, and the quiz as one section among many — not regex-parsed text + a bare 5-MCQ.
- Current state: `homework.html:75–82` reads only `data.homework_block` (legacy text) and `data.quiz_questions`, ignoring `data.homework_structured` that the API already ships.
- Architecture:
  - Frontend: redesign `homework.html` → narrative header, task cards, collapsible quiz. Fall back to legacy rendering when `homework_structured` is absent (older lesson codes).
  - Endpoint: `GET /api/h/{code}` — no change needed
  - No schema / prompt changes

**[ ] US-4.2.1-rev: Resolve adventure format enum**
- The prompt advertises 7 format strings (`adventure | investigation | creative | story_problem | detective | game | letter_journal` in `prompts.py:193`); the roadmap's original US-4.2.1 specified a different 6-value enum (`detective | expedition | design_challenge | story_mission | relay_puzzle | community_interview`). Pick one set, lock it as a `Literal[...]` on `HomeworkBlock.format`, and align the prompt. The UI in V4.2a will force this decision.

#### V4.2b — Safety & approval (defer until V4.2a ships)

**[~] US-4.2.3: Teacher feasibility review** (model shipped; endpoint + UI pending)
- As a teacher, before assigning a homework adventure, I see safety notes surfaced from `TeacherNotesBlock.safety_notes` and can approve or request regeneration.
- Architecture:
  - Model: `safety_notes` already on `TeacherNotesBlock` (done)
  - Endpoint: `POST /api/homework/{code}/approve` (new — `api/homework.py`)
  - Data: `homework_codes.approved_at` timestamp (new migration)
  - Web UI: approval toggle on teacher-facing homework instant view

---

### V4.3 — Student Identity + Community

**Goal:** Students gain progressive identity (teacher-scoped first). Teachers can publish lessons to the community. Peer rating begins.

**The community flywheel (why this phase exists).** Teachers publish lessons → peers discover and use them → students engage via two signals: **(a) completion** (did they finish the homework?) and **(b) rating** (1–5 stars + reaction after submitting, US-4.3.8) → those signals plus teacher reflections (US-4.3.6) and peer endorsements aggregate into a teacher **reputation score** (US-4.4.10) → discovery ranks by a blend of teacher judgment and earned reputation → the best content surfaces, the strongest teachers earn visibility and subject-lead eligibility. Co-moderation, co-discussion (US-4.4.8), and subject-lead curation (US-4.4.9) sit on top of this spine. The goal is not a content library but a **self-improving crowd-curated curriculum**, grounded in teachers' pedagogical judgment and validated by students' observed engagement.

#### User Stories

**[ ] US-4.3.1: Progressive student identity (Layer 1)**
- As a teacher, when my student submits a quiz as "Amina, SS2A", I can see Amina's scores across all my homework codes — without Amina creating an account.
- Architecture:
  - Model: `src/classgen/core/student.py` → `StudentIdentity(name, class_name, teacher_phone)` with collision detection
  - Table: New `students` table: `id, name, class_name, teacher_phone, parent_phone_last4 nullable, created_at`
  - Migration: `003_add_students.sql` — create table, update `quiz_submissions` to reference `student_id`
  - Endpoint: `GET /api/teacher/{phone}/students` — list students with cross-homework scores

**[ ] US-4.3.2: Student progress view**
- As a student (or parent), when I visit my progress page, I see my scores across subjects, my adventure completion history, and which topics I struggled with.
- Architecture:
  - Endpoint: `GET /api/student/{id}/progress` — aggregated scores by subject
  - Frontend: New `progress.html` page

**[ ] US-4.3.3: Teacher publishes lesson to community**
- As a teacher, I can mark a lesson as "shared" so other teachers can discover and use it. My name, school, and subject are shown. I retain ownership.
- Architecture:
  - Table: `community_lessons` → `id, homework_code, teacher_phone, subject, class_level, shared_at, rating_avg, use_count`
  - Endpoint: `POST /api/lesson/{code}/share`
  - Data: `src/classgen/data/community.py` — new module

**[ ] US-4.3.4: Peer rating and discovery**
- As a teacher, I can browse community lessons by subject and class, see ratings and use counts, and use a shared lesson with my class (creating my own homework code from the shared content).
- Architecture:
  - Endpoint: `GET /api/community/lessons?subject=Biology&class=SS2` — paginated, sorted by rating
  - Endpoint: `POST /api/community/lessons/{id}/rate` — 1-5 star rating
  - Endpoint: `POST /api/community/lessons/{id}/use` — fork lesson, create new homework code

**[ ] US-4.3.5: Subject/class cohort directory**
- As a teacher in Nigeria teaching SS2 Biology, when I open the community page I see a feed of other teachers teaching the same subject/class in the same country/region this week, with links to the lessons they generated. Turns the platform from a content library into a peer cohort — "I am not alone teaching this topic this week."
- Architecture:
  - Endpoint: `GET /api/community/cohort?subject=Biology&class=SS2&country=Nigeria&week=current`
  - Data: reads existing `lesson_history` joined with `teachers` — no schema change
  - Frontend: cohort panel on community discovery page
  - Privacy: only teachers who have opted into community publishing are listed (reuses US-4.3.3 share flag); lesson codes link to the community listing, never expose raw homework links

**[ ] US-4.3.6: Teacher reflection cards (qualitative signal)**
- As a teacher, after I use a shared community lesson with my class I'm prompted (one day later) to leave a short reflection — *what worked*, *what I changed*, *my class's reaction*. Reflections appear on the community lesson card beneath the star rating, giving future users the *why*, not just the *how many stars*. This is the qualitative signal that turns ratings into a conversation.
- Architecture:
  - Table: `lesson_reflections` → `id, community_lesson_id, teacher_phone, what_worked text, what_changed text, class_reaction text, created_at`
  - Migration: `009_add_lesson_reflections.sql`
  - Endpoints: `POST /api/community/lessons/{id}/reflect`, `GET /api/community/lessons/{id}/reflections` (paginated, recent first)
  - UI: prompt delivered via web push + WhatsApp 24h after lesson generation when the teacher forked a community lesson (reuses V4.1 push infra); reflections shown inline on the community lesson card

**[ ] US-4.3.7: Student engagement on community lesson cards (quantitative signal)**
- As a teacher browsing community lessons, each card shows the aggregate student signal — submission count, completion rate, average quiz score, **and the average student rating from US-4.3.8** — across every class that has ever used this lesson. The quantitative signal sits next to the qualitative reflections, so I can judge a lesson on both teacher craft and observed student effect.
- Two distinct rating streams feed this card (do not conflate):
  - **Teacher → lesson** star rating (US-4.3.4): peer craft judgment. "Would I teach this?"
  - **Student → homework** star + reaction (US-4.3.8): the learner's voice. "Did this land?"
- Architecture:
  - Endpoint: `GET /api/community/lessons` response gains `engagement: {submissions, completion_rate, avg_score, avg_student_rating, reaction_histogram}` computed across all `homework_codes` forked from the same `community_lesson_id`
  - Data: joins `community_lessons` ← `homework_codes` ← `quiz_submissions` + `homework_ratings` — no schema change (reads the new table US-4.3.8 introduces)
  - Ranking: discovery sort gains `?sort=engagement` and `?sort=student_rating`; default remains `rating` until data volume justifies a composite

**[ ] US-4.3.8: Student rates homework after submission**
- As a student, after submitting a homework quiz I can leave a quick 1–5 star rating and optionally tap a reaction chip (`fun` / `hard` / `confusing` / `boring` / `loved it`). Anonymous — no name required, distinct from the quiz submission identity. This is the **student's voice** returning to the teacher and, via US-4.3.7, to the community.
- Architecture:
  - Table: `homework_ratings` → `id, homework_code, rating int (1-5), reaction text nullable, created_at` (no student identity — pure signal, avoids coercion)
  - Migration: `013_add_homework_ratings.sql`
  - Endpoint: `POST /h/{code}/rate` body `{ rating, reaction? }`
  - Frontend: star widget + reaction chips appear on the submit-confirmation card in `homework.html`; optional skip
  - Aggregation: `avg_student_rating` per `homework_code` → bubbled up per `community_lesson_id` (see US-4.3.7) and per teacher (see US-4.4.10)

---

### V4.4 — Teacher Trust Network + Analytics

**Goal:** Teachers earn trust through verified credentials and engagement. Content is co-moderated. Analytics flow from teacher to ministry.

#### User Stories

**[ ] US-4.4.1: Teacher verification**
- As a teacher, I can add my certification number, school affiliation, and teaching experience to my profile. School admin confirms the affiliation. Verified teachers get a badge and their shared content is prioritized.
- Architecture:
  - Model: `src/classgen/core/teacher.py` → `TrustLevel` enum (teacher, verified, subject_lead, school_admin, reviewer)
  - Table: `teacher_verification` → `teacher_phone, certification_number, school_slug, years_experience, verified_at, verified_by`
  - Migration: `004_add_verification.sql`
  - Endpoint: `POST /api/teacher/verify`, `POST /api/school/{slug}/confirm-teacher`

**[ ] US-4.4.2: Content flagging and peer review**
- As a verified teacher, I can flag a community lesson for inaccuracy, safety concern, or inappropriate content. Flags are reviewed by subject leads (peer teachers with high trust scores), not a central team.
- Architecture:
  - Table: `content_flags` → `id, lesson_id, flagged_by, reason, status (open/confirmed/dismissed), reviewed_by`
  - Endpoint: `POST /api/community/lessons/{id}/flag`, `POST /api/community/flags/{id}/review`

**[ ] US-4.4.3: Community-verified content**
- As a teacher browsing community lessons, I can see which lessons are "community verified" — endorsed by multiple certified teachers across different schools.
- Architecture:
  - Table: `lesson_endorsements` → `lesson_id, teacher_phone, endorsed_at`
  - Logic: Lesson becomes "verified" when endorsed by N verified teachers from M different schools
  - Endpoint: `POST /api/community/lessons/{id}/endorse`

**[ ] US-4.4.4: Lesson remix**
- As a teacher, I can fork a community-verified lesson, adapt blocks for my context (different opener, localized activity), and publish the remix. The original is credited.
- Architecture:
  - Table: `community_lessons.forked_from` — nullable reference to parent lesson
  - Endpoint: `POST /api/community/lessons/{id}/remix` → creates new lesson with modified blocks
  - Model: `LessonPack` supports block-level replacement

**[ ] US-4.4.5: Teacher analytics dashboard**
- As a teacher, I see a dashboard with: lessons generated this week/month, student engagement (quiz scores, adventure completion), my hardest topics (where students score lowest), and peer comparison (how my engagement compares to subject average).
- Architecture:
  - Endpoint: `GET /api/teacher/{phone}/analytics` — aggregated metrics
  - Data: Computed from `homework_codes`, `quiz_submissions`, `lesson_history`, `community_lessons`

**[ ] US-4.4.6: School admin analytics**
- As a school admin, I see: which teachers are active, subject coverage gaps (topics not taught with N weeks left in term), student performance trends, and homework completion rates.
- Architecture:
  - Endpoint: `GET /api/school/{slug}/analytics` — anonymized student data, teacher activity
  - Data: Aggregated from teacher-scoped data within the school

**[ ] US-4.4.7: Anonymized regional analytics**
- As a ministry/curriculum body, I see anonymized aggregate data: topic difficulty nationwide (which topics have lowest scores), format effectiveness (adventure vs quiz-only completion rates), regional patterns, and novel teaching approaches emerging from the community.
- Architecture:
  - Endpoint: `GET /api/analytics/regional?country=NG&region=Lagos` — no student PII, no teacher names
  - Data: Aggregated from `lesson_history`, `quiz_submissions`, `community_lessons`, grouped by region/subject/class
  - Model: Teacher is the anchor entity — `Teacher 454F32 teaches 2 subjects, 55 students, avg 72%`

**[ ] US-4.4.8: Block-level comments on shared lessons (co-discussion)**
- As a teacher viewing a community-verified lesson, I can leave a comment on any individual block ("I replaced the analogy with a farming one, my students got it faster"). Comments thread inline on each block card. This is **co-discussion, not co-editing** — cheapest way to capture colleague-to-colleague know-how without the coordination cost of shared drafts.
- Architecture:
  - Table: `lesson_block_comments` → `id, community_lesson_id, block_type (opener|explain|activity|homework|teacher_notes), teacher_phone, comment_text, parent_comment_id nullable, created_at`
  - Migration: `010_add_lesson_block_comments.sql`
  - Endpoints: `POST /api/community/lessons/{id}/comments` (body includes `block_type`), `GET /api/community/lessons/{id}/comments?block=opener`
  - UI: comment count badge on each block card on community lesson page; click expands thread with reply form

**[ ] US-4.4.9: Subject-lead weekly picks (editorial + in-community promotion)**
- As a Subject Lead (verified teacher with high trust in a subject, per US-4.4.1 `TrustLevel`), I curate a weekly shortlist of 3–5 standout lessons per subject/class I lead. My picks appear in a banner atop the community discovery feed for that subject, with my note on why each was picked. This adds editorial narrative and a promotion channel teachers can trust — no paid boost, no algorithm-only ranking.
- Architecture:
  - Table: `weekly_picks` → `id, curator_phone, subject, class_level, week_start_date, community_lesson_id, curator_note text, created_at`
  - Migration: `011_add_weekly_picks.sql`
  - Endpoints: `POST /api/community/picks` (curator-only), `GET /api/community/picks?subject=Biology&class=SS2&week=current`
  - Permissions: enforced at endpoint via `TrustLevel >= subject_lead` check
  - UI: "This week's picks from {curator}" banner atop community discovery; curator's name links to their public profile

**[ ] US-4.4.10: Teacher reputation score (earned, not credentialed)**
- As a teacher, my public profile shows a **reputation score** I earn from: (a) my students actually completing the homework I assign (`quiz_submissions`), (b) the star ratings those students give after completing (US-4.3.8 `homework_ratings`), (c) other teachers remixing my shared lessons (US-4.4.4), and (d) peer endorsements (US-4.4.3). Reputation is **earned**, complementary to `TrustLevel` (US-4.4.1) which is credentialed. Reputation feeds community discovery ranking and subject-lead eligibility.
- The score is **transparent**: the profile shows the breakdown — "Students completed: 1,247 · Avg student rating: 4.3 · Remixes of my lessons: 18 · Peer endorsements: 9" — not an opaque number. Teachers trust what they can audit.
- Architecture:
  - Derived (not stored) — computed from existing and V4.3/V4.4 tables: `quiz_submissions`, `homework_ratings`, `community_lessons.use_count` / `forked_from`, `lesson_endorsements`
  - Endpoint: `GET /api/teacher/{phone}/reputation` returns `{ completions, avg_student_rating, remix_count, endorsement_count, composite }`
  - Formula (v1, tunable, documented in `services/reputation.py`):
    `composite = completions + Σ(student_ratings) + 2·remix_count + 3·endorsement_count`
  - Attribution on remixes: forking teacher B gets primary credit (they assigned it to their class); original teacher A gets smaller upstream credit per completion on forks — open-source-style chain attribution, `upstream_weight = 0.25`
  - UI: reputation card on public profile `/t/{slug}`, next to `TrustLevel` badge
  - Ranking: US-4.3.7's `?sort=engagement` becomes reputation-aware once this ships; subject-lead eligibility (US-4.4.1) gains an explicit reputation threshold rather than the current implicit "high trust score"
  - Safeguards: rate-limited signals per student per homework (one rating only); spike detection flags suspicious reputation growth for subject-lead review

---

### V4.5 — Engagement & Generation Delight (deferred)

**Goal:** Make lessons **fun** — on both sides of the content. V4.2 ships the adventure *data*; V4.5 ships the UX that carries the metaphor through to students and the generation levers that make authoring feel playful to teachers. Not required for the community flywheel (V4.3/V4.4) to function; multiplies engagement once the flywheel is running.

**[ ] US-4.5.1: Homework streaks + progression character**
- As a student with a persistent identity in my teacher's class (US-4.3.1), my homework page shows a streak counter ("5 homeworks in a row"), a simple character that evolves with each completion, and encouraging copy when I break or recover a streak. Teacher-toggleable per class.
- Architecture:
  - Data: derived from `quiz_submissions` grouped by `student_id` — no schema change
  - Frontend: streak widget + progression art on `/h/CODE`
  - Setting: `teacher.class_settings.show_streak` (per class) in `teachers` classes jsonb

**[ ] US-4.5.2: Serialized adventures**
- As a teacher generating multiple lessons for the same class/subject within a term, I can opt into "serialized mode" — adventure narratives carry recurring characters, settings, and a running arc across lessons. Students encounter the same detective team or expedition crew across weeks.
- Architecture:
  - Schema: add `adventure_state jsonb` (characters, setting, running_arc) on `lesson_history`
  - Migration: `012_add_adventure_state.sql`
  - Prompt: generator conditions on the prior lesson's `adventure_state` for the same (teacher, class, subject) tuple
  - Endpoint: `POST /api/teacher/class/{slug}/serialize` to opt in / opt out

**[ ] US-4.5.3: Teacher mood dial on generation**
- As a teacher, when requesting a lesson I can set mood parameters — `funnier`, `more_debate`, `more_kinesthetic`, `more_story`, `more_visual`. The generator conditions its prompt on these tokens. Small lever, big perceived-quality lift because teachers feel they're *directing*, not just receiving.
- Architecture:
  - Schema: `/api/chat` + `/api/chat/stream` request gain optional `mood: list[str]` (allow-listed values)
  - Prompt: `CLASSGEN_JSON_SYSTEM_PROMPT` appends "Lean into: {moods}" when set
  - Frontend: pill selector in composer (multi-select)
  - WhatsApp: `/mood funnier kinesthetic` command stored on teacher profile as default mood

**[ ] US-4.5.4: Block-level regeneration with critique**
- As a teacher, after receiving a lesson I can select any block and request a regeneration with a free-text critique — "rewrite the opener, my class found it boring"; "make the activity work for 50 students not 20". Other blocks are preserved. Turns generation into a conversation, not a one-shot.
- Architecture:
  - Endpoint: `POST /api/chat/regenerate-block` with `thread_id`, `lesson_code`, `block_type`, `critique`
  - Service: focused single-block prompt seeded with full lesson context for coherence
  - Frontend: "Rewrite block" button on each block card in web chat
  - WhatsApp: `rewrite opener: too boring` command (flow-engine dispatch)
  - Data: updates `lesson_json` in place; logs each regen with block_type + critique for future prompt tuning

---

## V5 — Internationalization & Market Expansion

**Goal:** Open ClassGen to non-English-speaking African markets. The current 14-country roster (Kenya, Rwanda, Tanzania, Uganda, Cameroon, Ghana, Nigeria, Botswana, South Africa, Zambia, Zimbabwe, India, UK, US) is English-speaking by intent — lessons, prompts, and UI all assume English. Demos are showing real interest in French, Portuguese, and Arabic markets, so this phase brings the platform to them.

**Sequencing.** US-5.1 (UI translation infrastructure) is a hard prerequisite for US-5.2 (new markets). Adding French countries to the dropdown without French interface strings would ship a half-translated experience that's worse than the current English-only scope.

**Out of scope for V5.** LLM lesson generation in non-English languages is a separate workstream — V5 ships the *interface* in the teacher's language; the *generated lesson content* still arrives in English from the model. Multi-language generation is a V6 concern (model + prompt engineering, glossary terms per curriculum, evaluation pipeline per language).

**[ ] US-5.1: Static UI translation infrastructure**
- As a Francophone or Lusophone teacher, all interface strings I see — intro slides, terms page, sidebar labels, command help, error messages, WhatsApp welcome, onboarding microcopy — render in my language. The platform detects my locale from my phone country code (or browser `Accept-Language` for web users with no profile yet) and lets me override it from the profile sidebar.
- Architecture:
  - Schema: add `locale text NOT NULL DEFAULT 'en'` to `teachers`. Migration `015_add_teacher_locale.sql`.
  - Catalog: extract every hardcoded UI string into per-locale message files (`src/classgen/i18n/messages/{locale}.json`). Server reads via a `t(key, locale)` helper; frontend reads via `/api/i18n/{locale}` (cached). Start with English as the source-of-truth catalog and stub `fr`, `pt` files.
  - Detection: extend `PHONE_LOCALES` to cover the new markets. Web fallback uses `Accept-Language` header parsing.
  - Endpoint: `PATCH /api/teacher/locale` (mirrors `/api/teacher/country`).
  - Frontend: `<html lang dir>` set per locale; sidebar gains a Language picker beneath Country.
  - WhatsApp: welcome message + command help + flow prompts all routed through `t()` keyed by `teacher.locale`.
  - RTL: not needed for French/Portuguese; flagged as US-5.1.RTL prerequisite if Arabic is added to V5.2.
  - Library choice: Babel server-side (already a dep), lightweight runtime catalog client-side (no React i18n framework — overkill for our string volume).
  - Coverage gate: a test enumerates every key in `en.json` and asserts every other locale catalog has the same keys (no missing translations slip in silently).

**[ ] US-5.2: Expand country support to non-English markets** *(depends on US-5.1)*
- As a teacher in Senegal, Ivory Coast, Mozambique, or Egypt, I can register and pick my country from the dropdown, the WhatsApp auto-detect recognizes my phone code, and the entire interface speaks my language.
- Markets to add (grouped by primary language tier):
  - **French (West Africa):** Senegal, Ivory Coast, Mali, Burkina Faso, DR Congo, Cameroon-Francophone (note: Cameroon is already in the dropdown — splits into anglophone/francophone via locale).
  - **Portuguese:** Mozambique, Angola.
  - **Arabic (RTL):** Egypt, Morocco. Requires US-5.1.RTL.
  - **Restoration:** Ethiopia (Amharic primary, English in education) and Malawi (English official + Chichewa) re-enter the dropdown once their primary language has a catalog.
- Architecture:
  - Migration `016_seed_v5_countries.sql` extends `supported_countries` with the new rows + their region assignments. New "North Africa" region for Egypt/Morocco; existing regions absorb the rest.
  - Update `i18n.py` `COUNTRY_REGIONS`, `COUNTRY_FLAGS`, `PHONE_COUNTRIES` in lockstep — invariant test (`test_phone_countries_subset_of_dropdown`) catches drift.
  - "What We Are NOT Building (Yet)" table updated to remove the English-only-scope note.

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
| US-4.3.5 | None (reads existing) | `api/community.py`, `services/community.py` | `GET /api/community/cohort` |
| US-4.3.6 | `lesson_reflections` (new) | `data/community.py`, `api/community.py` | `POST/GET /api/community/lessons/{id}/reflect(ions)` |
| US-4.3.7 | None (reads existing + `homework_ratings`) | `services/community.py` | `GET /api/community/lessons` (engagement payload + `?sort=engagement` / `?sort=student_rating`) |
| US-4.3.8 | `homework_ratings` (new) | `data/homework.py`, `api/homework.py`, `homework.html` | `POST /h/{code}/rate` |
| US-4.4.1 | `teacher_verification` (new) | `core/teacher.py`, `data/teachers.py` | `POST /api/teacher/verify` |
| US-4.4.2 | `content_flags` (new) | `data/community.py` | `POST /api/.../flag`, `.../review` |
| US-4.4.3 | `lesson_endorsements` (new) | `data/community.py` | `POST /api/.../endorse` |
| US-4.4.4 | `community_lessons.forked_from` | `data/community.py` | `POST /api/.../remix` |
| US-4.4.5 | None (reads existing) | `services/analytics.py` | `GET /api/teacher/{phone}/analytics` |
| US-4.4.6 | None (reads existing) | `services/analytics.py` | `GET /api/school/{slug}/analytics` |
| US-4.4.7 | None (reads existing) | `services/analytics.py` | `GET /api/analytics/regional` |
| US-4.4.8 | `lesson_block_comments` (new) | `data/community.py`, `api/community.py` | `POST/GET /api/community/lessons/{id}/comments` |
| US-4.4.9 | `weekly_picks` (new) | `data/community.py`, `api/community.py` | `POST/GET /api/community/picks` |
| US-4.4.10 | None (derived from existing + `homework_ratings`) | `services/reputation.py` (new), `api/teacher.py`, `/t/{slug}` template | `GET /api/teacher/{phone}/reputation` |
| US-4.5.1 | None (reads existing) | `api/homework.py`, `homework.html` | `GET /api/h/{code}` (streak payload) |
| US-4.5.2 | `lesson_history.adventure_state` (add col) | `services/llm.py`, `content/prompts.py`, `api/teacher.py` | `POST /api/teacher/class/{slug}/serialize` |
| US-4.5.3 | None | `services/llm.py`, `api/chat.py`, `api/webhook.py`, `content/prompts.py` | `POST /api/chat` (+mood field) |
| US-4.5.4 | None (updates existing `lesson_json`) | `services/llm.py`, `api/chat.py` | `POST /api/chat/regenerate-block` |
| US-5.1 | `teachers.locale` (add col) | `i18n/messages/{locale}.json` (new), `i18n.py` (t() helper), all UI surfaces (`channels/`, `commands/`, `index.html`, `terms.html`) | `GET /api/i18n/{locale}`, `PATCH /api/teacher/locale` |
| US-5.2 | `supported_countries` (insert rows; new "North Africa" region) | `i18n.py` (`COUNTRY_REGIONS`, `COUNTRY_FLAGS`, `PHONE_COUNTRIES`), seed migration | `GET /api/teacher/countries` (no shape change) |

## Migration Sequence

| # | Status | File | Phase | Description |
|---|---|---|---|---|
| 001 | [x] | `001_baseline.sql` | V3.1 | Marker for init.sql schema |
| 002 | [x] | `002_add_updated_at.sql` | V3.1 | updated_at columns + triggers |
| 003 | [x] | `003_add_lesson_json.sql` | V4.1 | Add `lesson_json jsonb` to `homework_codes` and `lesson_cache` |
| 004 | [x] | `004_add_onboarded_at.sql` | V4.1 | Onboarding consent timestamp on `teachers` |
| 005 | [x] | `005_add_country.sql` | V4.1 | Teacher country for curriculum-aware prompt injection |
| 006 | [x] | `006_create_supported_countries.sql` | V4.1 | `supported_countries` reference table (name PK, flag, region, sort_order) seeded with the 14 English-speaking markets. |
| 007 | [ ] | `007_add_students.sql` | V4.3 | Create `students` table. Add `student_id` to `quiz_submissions`. |
| 008 | [ ] | `008_add_community.sql` | V4.3 | Create `community_lessons`, indexes on subject/class/rating. |
| 009 | [ ] | `009_add_verification.sql` | V4.4 | Create `teacher_verification`, `content_flags`, `lesson_endorsements`. |
| 010 | [ ] | `010_add_lesson_reflections.sql` | V4.3 | Create `lesson_reflections` (what_worked / what_changed / class_reaction per community lesson). |
| 011 | [ ] | `011_add_lesson_block_comments.sql` | V4.4 | Create `lesson_block_comments` for co-discussion on shared lessons. |
| 012 | [ ] | `012_add_weekly_picks.sql` | V4.4 | Create `weekly_picks` for subject-lead editorial curation. |
| 013 | [ ] | `013_add_adventure_state.sql` | V4.5 | Add `adventure_state jsonb` to `lesson_history` for serialized adventures. |
| 014 | [ ] | `014_add_homework_ratings.sql` | V4.3 | Create `homework_ratings` (anonymous 1-5 star + reaction per submission) — feeds reputation + community cards. |
| 015 | [ ] | `015_add_teacher_locale.sql` | V5 | Add `locale text NOT NULL DEFAULT 'en'` to `teachers` for UI translation. |
| 016 | [ ] | `016_seed_v5_countries.sql` | V5 | Extend `supported_countries` with French/Portuguese/Arabic markets + new "North Africa" region. |

---

## Implementation Order

```
V4.0  Restructure to src/classgen/         ✅ DONE (April 2026)
  ↓
V4.1  Structured output + adapters + SSE   ✅ DONE (April 2026, flag-gated)
  ↓
V4.2  Adventure homework                   ← NEXT: content quality leap
       (V4.2a — adventure UI priority; V4.2b — approval flow deferred)
  ↓
V4.3  Student identity + community         ← network effects begin
       (cohort directory, teacher reflections = qualitative signal;
        student completion + student rating = quantitative signal,
        both aggregated on community lesson cards)
  ↓
V4.4  Trust network + analytics            ← platform intelligence
       (block-level comments = co-discussion; subject-lead picks =
        editorial narrative + in-community promotion; teacher
        reputation = earned score from student engagement + ratings
        + remixes + endorsements, feeds ranking + subject-lead gate)
  ↓
V4.5  Engagement & generation delight      ← fun layer (deferred)
       (streaks, serialized adventures, mood dial, block regen)
  ↓
V5    Internationalization & market expansion ← unlock non-English markets
       (US-5.1 UI translation infra → US-5.2 French/Portuguese/Arabic
        markets; demos showing real interest)
```

**Dependencies between V4.3 / V4.4 / V4.5.** V4.3 ships the flywheel spine; V4.4 adds trust, moderation, editorial, and co-discussion on top; V4.5 can slot in at any point once structured output is on in production (it reads the same data). Some V4.5 stories (US-4.5.1 streaks) depend on V4.3.1 student identity.

**V5 is independent of V4.2–4.5.** It can begin in parallel as soon as the team has bandwidth — none of the V4 features assume English. The strict ordering inside V5 is US-5.1 before US-5.2 (translation infra before adding markets that depend on it).

Each phase is independently deployable. V4.2 onward adds new capabilities.
