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

### V2.1 -- Parent & Student Layer

Goal: extend the value chain beyond the classroom.

Changes:
- [ ] Opt-in parent WhatsApp digest (weekly per subject)
- [ ] Student progress tracking (across homework code submissions)
- [ ] Class leaderboard (opt-in, visible to teacher only by default)
- [ ] "Study mode" -- student can request a recap of any lesson via WhatsApp

---

### V3.0 -- Platform

Goal: ClassGen becomes the tool a school subscribes to, not just individual teachers.

Changes:
- [ ] Curriculum mapping by country and exam board
- [ ] School admin dashboard (which teachers are active, lesson coverage)
- [ ] Paystack integration for premium features
- [ ] Printable worksheet generator (formatted PDFs with game boards, fill-in stories)
- [ ] Theme customization (school branding on PDFs and profile pages)
- [ ] Multi-language support (French, Yoruba, Hausa, Swahili, etc.)

---

## Shared Technical Modules

These modules cut across multiple phases. Building them right the first time avoids rewriting later.

### 1. WhatsApp Command Router (`commands.py`)

**Used by:** V1.3 (session reset), V2.0 (profile commands), V2.1 (parent opt-in, study mode)

Currently the webhook handler has inline `if body.strip().lower() in (...)` checks. As commands grow, this becomes unmanageable. Extract a command router that:
- Matches incoming text against registered commands (exact match, prefix, regex)
- Falls through to the LLM lesson generator if no command matches
- Returns a structured response (text reply, optional media, optional session side-effects)

```
V1.3:  "new", "reset", "new lesson", "start over"
V2.0:  "register", "my page", "my results CODE", "add class: SS2 Biology", "hide lesson"
V2.1:  "subscribe parent +234...", "study TOPIC"
```

### 2. Data Access Layer (`db.py`)

**Used by:** every phase

Currently `utils.py` mixes OpenRouter client, Supabase client, session ops, homework ops, and quiz ops in one file. As we add `teachers`, `classes`, `lessons` tables (V2.0), `parent_subscriptions` (V2.1), and `schools` (V3.0), this file will explode.

Split into:
- `db.py` -- Supabase/Postgres client init, in-memory fallback dict, shared helpers
- `utils.py` -- OpenRouter client only (renamed or kept slim)

All table operations go through `db.py` with consistent patterns:
- `save_X()`, `get_X()`, `list_X()`, `delete_X()`
- Every function handles both Supabase and in-memory paths
- Timestamps always UTC ISO format

### 3. Teacher Identity (`db.py` teacher ops)

**Used by:** V2.0 (registration, profiles), V2.1 (parent links, progress), V3.0 (school admin)

The teacher's phone number is already the session key. V2.0 formalises this into a `teachers` table. Design it once:
- Phone number is the unique identifier (not an auto-generated ID)
- Slug derived from display name (for profile URL)
- Every lesson and homework code links back to the teacher
- Session history links to the teacher
- This is the join point for all downstream features (parents, schools, billing)

### 4. Lightweight Page Templates (`templates/`)

**Used by:** V1.2 (homework, results), V2.0 (teacher profile), V2.1 (student progress), V3.0 (admin dashboard)

Currently 3 standalone HTML files with duplicated CSS (same card styles, same font stack, same color scheme). V2.0 adds a teacher profile page, V3.0 adds an admin dashboard.

Strategy: **Jinja2 templates with a shared base.** FastAPI supports Jinja2 natively. One `base.html` with the shared `<head>`, styles, and layout. Each page extends it. This keeps pages lightweight (no JS framework) while avoiding copy-paste drift.

```
templates/
  base.html          -- shared head, styles, responsive layout
  homework.html      -- student quiz page (extends base)
  results.html       -- teacher results dashboard (extends base)
  profile.html       -- teacher public profile (V2.0)
  admin.html         -- school admin dashboard (V3.0)
```

### 5. Outbound Messaging (`messaging.py`)

**Used by:** V2.0 (profile URL reply, results summary), V2.1 (parent digest), V3.0 (school notifications)

Currently Twilio is only used for inbound webhook responses (TwiML). Outbound messaging (sending a message proactively) requires the Twilio REST API client. This is needed for:
- Sending quiz results summaries to teachers after students submit
- Weekly parent digests
- School admin notifications

One module, one Twilio client, consistent message formatting.

---

## What We Are NOT Building

| Idea | Why not |
|---|---|
| Student mobile app | Exercise books are the platform. A web page with a homework code is enough. |
| LMS / Moodle competitor | We generate content, we don't manage courses. |
| AI tutor for students | Our user is the teacher. Students benefit through the teacher. |
| Video content | Bandwidth constraints. Text + teacher delivery is more reliable. |
| Complex gamification | Leaderboards maybe. But the game IS the homework format, not a separate system. |

---

## Immediate Next Steps

1. ~~Rewrite the system prompt for content quality.~~ DONE (V1.1)
2. ~~Build homework code infrastructure.~~ DONE (V1.2)
3. ~~Fix V1.3 critical bugs.~~ DONE (V1.3)
4. ~~Set up CI (pytest + ruff on push).~~ DONE (V1.3)
5. Extract shared modules (command router, db layer, templates) -- foundation for V2.0.
6. Build V2.0 teacher profiles: registration, profile page, lesson history.
7. Generate 3 sample packs (Mathematics, Biology, English) and test with 5 real teachers.
8. Build outbound Twilio messaging for quiz results and teacher notifications.
