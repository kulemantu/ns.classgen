# ClassGen V4 Design Spec — Structured Output, Adaptive Rendering & Education Intelligence

Confidential — Working Draft | April 2026

---

## Why This Document Exists

ClassGen currently returns lesson packs as blocks of plain text parsed with regex. Both WhatsApp and the web UI receive the same raw string. This limits:

- **Web UX** — the chat shows a text blob where it could show rich, navigable cards
- **Homework** — quizzes are auto-generated in a separate LLM call, disconnected from the narrative
- **Analytics** — engagement data is trapped in unstructured text
- **Community** — lessons can't be compared, remixed, or surfaced without structured metadata

The structured output schema is the **data spine** of the platform. Every lesson block, activity type, quiz response, and engagement signal becomes a queryable, aggregatable, shareable unit of educational intelligence.

This spec covers the schema, rendering adapters, homework-as-adventure model, progressive student identity, teacher trust network, and analytics flywheel.

---

## 1. Structured Output Schema

### 1.1 Lesson Pack (top-level)

The LLM returns a single JSON object per lesson generation. The system prompt defines the schema; the model fills it.

```jsonc
{
  "version": "4.0",
  "meta": {
    "subject": "Biology",
    "topic": "Photosynthesis",
    "class_level": "SS2",
    "exam_board": "WAEC",
    "duration_minutes": 40,
    "language": "en",
    "bilingual": null          // or "yo" for English+Yoruba
  },
  "blocks": [
    { "type": "opener",        ... },
    { "type": "explain",       ... },
    { "type": "activity",      ... },
    { "type": "homework",      ... },
    { "type": "teacher_notes", ... }
  ]
}
```

### 1.2 Block Types

Each block has a `type`, `title`, `body`, and type-specific fields.

**opener**
```jsonc
{
  "type": "opener",
  "title": "What if photosynthesis stopped tomorrow?",
  "body": "Ask students: 'If every plant on Earth stopped making food from sunlight right now, how long before we feel it?' Give them 10 seconds to guess. The answer is terrifying...",
  "format": "what_if",          // what_if | demonstration | challenge | story_cold_open
  "duration_minutes": 2,
  "props": []                   // physical items needed, if any
}
```

**explain**
```jsonc
{
  "type": "explain",
  "title": "The Factory Inside Every Leaf",
  "body": "...",                // plain language explanation
  "wow_fact": "A single tree produces enough oxygen for 2 people for a year.",
  "analogy": "Think of a leaf as a tiny solar-powered factory...",
  "key_terms": [
    { "term": "chlorophyll", "definition": "The green pigment that captures sunlight" },
    { "term": "glucose",     "definition": "The sugar plants make as food" }
  ],
  "equation": "6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂"   // null if not applicable
}
```

**activity**
```jsonc
{
  "type": "activity",
  "title": "Photosynthesis Relay Race",
  "body": "...",                // full instructions
  "format": "relay_race",      // relay_race | group_challenge | debate | gallery_walk | think_pair_share | quiz_battle
  "group_size": 5,
  "duration_minutes": 12,
  "materials": ["exercise book", "pen", "chalk"],
  "rules": ["...", "..."],
  "expected_outcome": "Each team correctly sequences the 6 steps of photosynthesis."
}
```

**homework** (see Section 3 for the adventure model)
```jsonc
{
  "type": "homework",
  "title": "The Oxygen Detective",
  "format": "adventure",       // adventure | investigation | creative | story_problem | detective | game | letter_journal
  "narrative": "You are a science detective hired by the Ministry of Agriculture...",
  "tasks": [
    {
      "id": "clue_1",
      "instruction": "Visit any garden or farm near your home. Count how many different plants you can see. Write each name.",
      "type": "real_world",    // real_world | calculation | comprehension | creative | observation
      "clue": "The number of plant types you find is the first digit of the case code.",
      "exercise_book_format": "List with sketches"
    },
    {
      "id": "clue_2",
      "instruction": "Using the photosynthesis equation, calculate how many CO₂ molecules are needed for 3 glucose molecules.",
      "type": "calculation",
      "clue": "Your answer is the second part of the case code.",
      "exercise_book_format": "Show working, circle answer"
    }
  ],
  "completion": "Combine your clues to form the case code: [plant_count]-[co2_answer]. Write your detective report in one paragraph explaining why photosynthesis matters to the farm you visited.",
  "assessment_tip": "Check for: correct equation application, real plant names (not invented), and a report that connects photosynthesis to food production.",
  "quiz": [
    {
      "question": "What gas do plants absorb during photosynthesis?",
      "options": ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"],
      "correct": 1,
      "explanation": "Plants absorb CO₂ and release O₂."
    }
    // ... 4 more
  ]
}
```

**teacher_notes**
```jsonc
{
  "type": "teacher_notes",
  "expected_answers": ["6 × 3 = 18 CO₂ molecules", "..."],
  "common_mistakes": ["Confusing what plants absorb vs release", "..."],
  "quick_assessment": "If a student can explain why covering a plant kills it, they understood.",
  "next_lesson_link": "This connects to cellular respiration — the reverse process.",
  "exam_tip": "WAEC 2024 Q3 tested the balanced equation. Ensure students can write it from memory.",
  "safety_notes": null          // for activities involving real-world interaction
}
```

### 1.3 Why JSON, Not Markdown Blocks

| Concern | Markdown blocks (current) | Structured JSON |
|---|---|---|
| Parsing | Regex, fragile | Native `json.loads()` |
| Rendering | Same blob everywhere | Adapter per channel |
| Analytics | Can't query "how many adventure homeworks were assigned this week" | Every field is queryable |
| Remix | Copy entire text blob | Replace one block, keep the rest |
| Caching | Cache by text hash | Cache by (subject, topic, class, block_type) |
| Streaming | Stream text tokens | Stream JSON incrementally, render block-by-block |
| Community | Can't compare lessons structurally | "Show me all SS2 Biology openers rated 4+" |

### 1.4 LLM Integration

The system prompt specifies the JSON schema. The model returns JSON directly (OpenRouter supports `response_format: { type: "json_object" }` for compatible models). A validation layer checks the response against the schema before storage. Malformed responses fall back to raw text with a warning.

The quiz is embedded IN the homework block — not a separate LLM call. This eliminates the current two-call pattern and ensures quiz questions relate directly to the adventure narrative.

---

## 2. Channel Adapters

The same JSON lesson pack renders differently per channel. Each adapter transforms the structured data into the format appropriate for its medium.

### 2.1 Adapter Interface

```
lesson_pack (JSON) → adapter.render(lesson_pack) → channel-specific output
```

Adapters:

| Adapter | Output | Use case |
|---|---|---|
| `web` | Rich HTML cards with icons, separators, collapsible sections, action buttons | Chat UI instant views |
| `whatsapp` | Plain text summary with dictation-ready formatting | Twilio message |
| `pdf` | Formatted document with headers, page breaks, print-ready layout | Download / print |
| `sms` | Minimal text: topic + homework code + quiz link | Feature phone fallback |
| `audio` | SSML or plain text script optimized for TTS | Voice-narrated prep |
| `chalkboard` | Minimal bullet points — what to write on the board | Dictation guide |

### 2.2 Web Adapter — Instant Views

The chat remains the primary interface. When a lesson pack arrives, the chat shows a **lesson card** — a compact summary with action buttons. Tapping a block opens an **instant view** (overlay panel).

```
┌─────────────────────────────────────┐
│  LESSON PACK                        │
│  SS2 Biology: Photosynthesis        │
│  40 min · WAEC · 5 blocks           │
│                                     │
│  ✦ "What if photosynthesis stopped  │
│     tomorrow?"                      │
│                                     │
│  ┌─────┐ ┌─────┐ ┌────────┐        │
│  │ 📖  │ │ 🎯  │ │ 🏠     │        │
│  │Teach│ │Play │ │Homework│        │
│  └─────┘ └─────┘ └────────┘        │
│                                     │
│  ⬇ PDF   📋 Homework: XKQT42       │
└─────────────────────────────────────┘
```

Tapping "Teach" opens the explain block as a rich panel. Tapping "Homework" opens the adventure narrative with tasks. The chat scroll position is preserved.

### 2.3 WhatsApp Adapter — Dictation Format

WhatsApp gets a summary the teacher can read aloud or dictate:

```
*LESSON PACK: Photosynthesis*
SS2 Biology · 40 min · WAEC

*OPENER* (2 min)
"What if photosynthesis stopped tomorrow?"

*TEACH* — The Factory Inside Every Leaf
💡 A single tree = oxygen for 2 people/year

*ACTIVITY* — Relay Race (12 min)
Groups of 5, sequence the 6 steps

*HOMEWORK* — The Oxygen Detective 🔍
Adventure code: XKQT42
Students visit: class.dater.world/h/XKQT42

📄 Full PDF: class.dater.world/dl/XKQT42.pdf
```

### 2.4 Streaming (SSE)

The web adapter receives the lesson pack as a **stream of blocks**. As each JSON block completes, it renders immediately — the opener appears in ~2 seconds while the model is still generating the explain block. This eliminates the current 10-20 second dead wait.

Implementation: FastAPI `StreamingResponse` with SSE events. The OpenRouter streaming API sends tokens; the server accumulates JSON, emits each completed block as an SSE event. The frontend renders block-by-block with a typing animation.

WhatsApp does not stream — it waits for the full response (Twilio doesn't support streaming).

---

## 3. Homework as Adventure

### 3.1 The Model

Current homework: 5 multiple-choice questions auto-generated in a second LLM call.

Proposed homework: a **narrative adventure** where the student is the main character. Real-world clues, calculations, observations, and creative tasks feed into a story. The exercise book captures everything. The digital quiz is a supplementary signal.

**Key properties:**

- **Story-embedded** — tasks are clues in a narrative, not standalone questions
- **Multi-modal** — tasks combine real-world observation, calculation, comprehension, and creativity
- **Exercise-book-native** — every task produces something written or drawn in the book
- **Community-anchored** — tasks reference local landmarks, shops, nature (teacher uses discretion for feasibility and safety)
- **Verifiable by teacher** — the exercise book IS the proof. Teacher spot-checks 30 books in 5 minutes using the assessment tip
- **Digitally supplemented** — the 5-question quiz validates conceptual understanding. The adventure validates application

### 3.2 Adventure Types

| Type | Description | Example |
|---|---|---|
| `detective` | Evidence + deduction. Student solves a case using lesson concepts. | "The school garden is dying on one side. Evidence: different pH levels..." |
| `expedition` | Real-world data collection. Student visits a place, records observations. | "Visit 3 shops. Record the price of 1kg of rice. Calculate % difference." |
| `design_challenge` | Student creates something in exercise book. | "Design a poster explaining photosynthesis to a JSS1 student." |
| `story_mission` | Student IS a character. Tasks advance the plot. | "You are hired by the Ministry of Agriculture to investigate..." |
| `relay_puzzle` | Clues from multiple tasks combine into a final answer. | "Clue 1 digit + Clue 2 digit = your case code. Write the report." |
| `community_interview` | Student asks a real person a question, records the answer. | "Ask an elder: what was this area like 30 years ago? Compare to your geography lesson." |

### 3.3 Exercise Book Format

Each homework task specifies an `exercise_book_format` — what the student should physically produce:

- `list_with_sketches` — numbered list with small drawings
- `show_working` — mathematical working with circled answer
- `paragraph` — continuous prose (detective report, diary entry, letter)
- `diagram` — labelled drawing with annotations
- `table` — rows and columns comparing data
- `comic_strip` — 4-6 panels with speech bubbles
- `map_or_route` — hand-drawn map with landmarks

### 3.4 Safety & Feasibility

For adventures involving real-world interaction (visiting shops, interviewing people, collecting specimens):

- The `teacher_notes.safety_notes` field flags any concerns
- The system prompt instructs the LLM to generate activities that are **doable near home, during daylight, without cost**
- Teacher reviews the adventure before assigning — the platform provides it, the teacher approves it
- AI assists teachers in judging feasibility: "This activity requires visiting a river. Is there one accessible to your students?"

---

## 4. Progressive Student Identity

### 4.1 Identity Layers

Identity starts minimal and grows additively. Each layer is **concatenatable** — the full identity is the chain of resolved layers.

| Layer | Scope | When it's added | Collision resolution |
|---|---|---|---|
| `name + class` | Teacher's classroom | First homework submission | Teacher already handles this (they know their students) |
| `+ last 4 of parent phone` | School | When name collisions occur across classes | Data schools already have |
| `+ school slug` | Town/region | When school onboards to ClassGen | Admin links teacher to school |
| `+ town code` (NRB, LAG) | Country | Cross-school analytics | Teacher profile data |
| `+ self-selected username` | Global | Student chooses to create persistent identity | Student picks username + secret hint/answer |

### 4.2 Identity Resolution

```
Layer 1:  "Amina" + "SS2A"              → unique within Mrs. Okafor's class
Layer 2:  + "4532"                       → unique within Greenfield Academy
Layer 3:  + "greenfield"                 → unique within Lagos
Layer 4:  + "LAG"                        → unique nationally
Layer 5:  + "amina_star" (self-chosen)   → globally addressable
```

The platform resolves identity at the minimum layer needed. Most students never go past Layer 1. Cross-teacher correlation happens at Layer 2+ via school admin.

### 4.3 What Identity Enables

| Layer | Unlocks |
|---|---|
| 1 | Teacher sees Amina's scores across homework codes |
| 2 | School admin sees Amina's performance across subjects/teachers |
| 3 | Anonymized: "SS2 Biology students in Lagos average 68% on photosynthesis" |
| 4 | Anonymized: "Nationwide, mole calculations are the #1 struggle in SS2 Chemistry" |
| 5 | Student sees their own progress history, earns achievements |

### 4.4 Privacy by Design

- Students are **never identifiable** above the teacher level without explicit school admin linkage
- Ministry/regulator analytics are always anonymized: `Teacher 454F32 teaches 2 subjects, 55 students, avg quiz score 72%`
- The teacher is the **regulated entity** — their certification, school affiliation, and region are the anchor points
- Student data is scoped to the teacher's domain. Cross-teacher correlation requires school admin action

---

## 5. Teacher Trust Network

### 5.1 The Problem

AI-generated content at scale needs moderation, fact-checking, safety review, and quality control. A centralized editorial team doesn't scale. A fully automated system can't catch cultural nuance, local relevance, or pedagogical judgment.

### 5.2 The Model: Distributed Teacher Governance

Teachers are **chosen by parents, endorsed by education bodies, and certified by institutions**. This existing trust infrastructure becomes the platform's moderation layer — a blockchain-style distributed network where:

- **Every teacher is a node** — they generate, review, rate, and remix content
- **Trust is earned and verifiable** — teaching certification, school affiliation, years of experience, peer endorsements
- **Consensus validates quality** — a lesson rated highly by 10 certified biology teachers in 3 different schools carries more weight than one teacher's 5-star rating
- **Co-moderation is built-in** — teachers flag inaccurate content, inappropriate activities, or safety concerns. Flags are reviewed by peer teachers, not a central team

### 5.3 Trust Signals

Each teacher accumulates trust through verifiable and community signals:

**Verifiable (teacher provides):**
- Teaching certification / license number
- School affiliation (confirmed by school admin)
- Subjects + class levels taught
- Region / country
- Years of experience

**Community-earned:**
- Lessons generated (volume)
- Lessons used by other teachers (adoption)
- Student engagement metrics on their lessons (quiz scores, completion rates)
- Peer ratings on shared content
- Flags raised on other content (accuracy, safety) that were confirmed by consensus
- Endorsements from other certified teachers

### 5.4 Content Lifecycle with Trust

```
1. GENERATE  — Teacher generates a lesson pack via AI
2. USE       — Teacher uses it in class, students engage (quiz, adventure)
3. SIGNAL    — Engagement data flows back (scores, completion, teacher rating)
4. SURFACE   — High-signal lessons appear in community suggestions
5. REVIEW    — Other teachers use, rate, and optionally flag issues
6. ENDORSE   — Peer teachers endorse ("I used this, it works")
7. CURATE    — Lessons with strong consensus become "community verified"
8. REMIX     — Teachers fork verified lessons, adapt for their context
9. AGGREGATE — Anonymized patterns inform curriculum insights
```

### 5.5 Governance Roles

| Role | How they earn it | What they can do |
|---|---|---|
| **Teacher** (default) | Registration + first lesson | Generate, use, rate, flag |
| **Verified Teacher** | Certification + school affiliation confirmed | All above + content visible in community, peer endorsements count |
| **Subject Lead** | High trust score in a subject + peer endorsements | All above + review flagged content, curate subject collections |
| **School Admin** | Appointed by school | Link student records, view school-wide analytics, confirm teacher affiliations |
| **Regional Reviewer** | Ministry appointment or community election | View anonymized regional analytics, escalate systemic content issues |

### 5.6 Why "Blockchain-Style"

Not literally a blockchain — but the same principles:

- **Distributed consensus** — no single authority decides if a lesson is good. Multiple independent teachers validate through use and rating
- **Immutable history** — a lesson's engagement history, ratings, and flags are permanent and auditable
- **Transparency** — teachers can see why a lesson is "community verified" (who endorsed it, what engagement data supports it)
- **Resistance to gaming** — trust comes from verified identity + consistent engagement signals, not just self-reporting
- **Progressive decentralization** — early on, ClassGen's AI and team set quality standards. Over time, the teacher network self-governs through earned trust

---

## 6. Analytics Flywheel

### 6.1 Data Flow

```
Teacher generates lesson (structured JSON)
  → stored with teacher ID, subject, class, school, region
    ↓
Students engage (quiz scores, adventure completion, ratings)
  → stored linked to homework code + student identity (teacher-scoped)
    ↓
Engagement signals aggregate
  → lesson-level: avg score, completion rate, teacher rating
  → teacher-level: lessons/week, student engagement, peer adoption
  → subject-level: hardest topics, most engaging formats, regional patterns
  → system-level: curriculum coverage, format effectiveness, seasonal trends
    ↓
Insights feed back
  → Teacher: "Your students scored 45% on mole calculations. Here's a remix of a lesson that scored 82% in Lagos."
  → School admin: "3 of 8 biology teachers haven't covered cell division yet. Term ends in 4 weeks."
  → Ministry: "Nationwide, adventure-format homework has 3x completion rate vs quiz-only."
  → Community: "This photosynthesis lesson was endorsed by 23 teachers across 4 countries."
```

### 6.2 What Structured Output Enables

Every field in the JSON schema becomes an analytics dimension:

- `homework.format: "adventure"` → compare completion rates by format type
- `activity.format: "relay_race"` → which classroom activities correlate with highest quiz scores?
- `explain.key_terms` → which terms appear most in low-scoring quizzes? (concept difficulty mapping)
- `opener.format: "what_if"` → do "what if" openers produce better engagement than "story cold open"?
- `homework.tasks[].type: "real_world"` → do lessons with real-world tasks get higher teacher ratings?

This is impossible with unstructured text. The structured schema makes ClassGen an **education research platform** by default, not by effort.

---

## 7. Implementation Sequence

### Phase 1: Schema + Web Adapter (immediate)

- Define JSON schema as a Pydantic model
- Update system prompt to request JSON output
- Validation layer: parse JSON, fall back to raw text if malformed
- Web adapter: render lesson cards with instant view overlays
- Backward compatible: WhatsApp adapter wraps JSON → plain text (same output as today)
- SSE streaming: FastAPI StreamingResponse, block-by-block rendering

### Phase 2: Adventure Homework (next)

- Extend homework block schema with adventure types, tasks, clues
- Redesign homework.html as a narrative experience (not just 5 MCQ questions)
- Exercise book format guidance rendered alongside tasks
- Teacher safety/feasibility review prompt

### Phase 3: Student Identity + Community (after feedback)

- Progressive identity model (Layer 1: name+class, scoped to teacher)
- Student progress tracking across homework codes
- Teacher content sharing: publish to community
- Peer rating and endorsement system

### Phase 4: Trust Network + Analytics (with adoption)

- Teacher verification flow (certification, school linkage)
- Community content discovery (search by subject, class, format, rating)
- Content flagging + peer review workflow
- Anonymized analytics dashboards (teacher, school, regional levels)
- Lesson remix: fork a community-verified lesson, adapt, republish

---

## 8. What We Are NOT Building (Yet)

| Idea | Why not now |
|---|---|
| Student mobile app | Exercise book is the platform. Web page with homework code is enough. |
| AI tutor for students | Teacher is the delivery mechanism. Student-facing AI dilutes the teacher's role. |
| Video content | Bandwidth constraints. Text + teacher performance + multi-sensory activities > video. |
| Real-time collaborative editing | Teachers remix asynchronously. Real-time collab is a different product. |
| Blockchain/crypto tokens | The trust model uses blockchain principles, not blockchain technology. |
| Full LMS | ClassGen generates content and measures engagement. It doesn't manage courses, schedules, or grades. |

---

## Appendix: Content Philosophy (from ROADMAP.md)

Every design decision in this spec serves these principles:

1. **Paper-first.** Every lesson pack must work perfectly when read aloud or written on a chalkboard. Technology is an enhancement layer, never a requirement.
2. **Teacher as performer.** The teacher is the delivery mechanism. Our content gives them material to *perform* — hooks, stories, challenges, surprises — not walls of text to dictate.
3. **Exercise book is the student's platform.** For most students, their exercise book is the only tool they take home. Homework must be designed to be completed in an exercise book with nothing else.
4. **Classroom is the environment.** Physical activities, group dynamics, movement, debate, presentation — the classroom is a multi-sensory learning space, not rows of silent desks.
5. **Teacher is the trust anchor.** Chosen by parents, endorsed by education bodies, certified by institutions. The platform's quality, safety, and governance flow through the teacher network.
