"""Shared test fixtures for V4.1 structured output tests."""

import json

# --- Structured JSON (V4.1) ---

SAMPLE_LESSON_JSON_DICT = {
    "version": "4.0",
    "meta": {
        "subject": "Biology",
        "topic": "Photosynthesis",
        "class_level": "SS2",
        "exam_board": "WAEC",
        "duration_minutes": 40,
        "language": "en",
        "bilingual": None,
    },
    "blocks": [
        {
            "type": "opener",
            "title": "What if photosynthesis stopped tomorrow?",
            "body": "Ask students: 'If every plant stopped making food from sunlight right now, how long before we feel it?'",
            "format": "what_if",
            "duration_minutes": 2,
            "props": [],
        },
        {
            "type": "explain",
            "title": "The Factory Inside Every Leaf",
            "body": "Think of each leaf as a tiny solar-powered factory that turns sunlight, water, and carbon dioxide into sugar and oxygen.",
            "wow_fact": "A single tree produces enough oxygen for 2 people for a year.",
            "analogy": "A leaf is like a solar-powered factory.",
            "key_terms": [
                {"term": "chlorophyll", "definition": "The green pigment that captures sunlight"},
                {"term": "glucose", "definition": "The sugar plants make as food"},
            ],
            "equation": "6CO\u2082 + 6H\u2082O \u2192 C\u2086H\u2081\u2082O\u2086 + 6O\u2082",
        },
        {
            "type": "activity",
            "title": "Photosynthesis Relay Race",
            "body": "Split class into teams of 5. Each team member must write one step of photosynthesis on the board in order.",
            "format": "relay_race",
            "group_size": 5,
            "duration_minutes": 12,
            "materials": ["exercise book", "pen", "chalk"],
            "rules": ["No looking at notes", "Must write in correct order"],
            "expected_outcome": "Each team correctly sequences the 6 steps of photosynthesis.",
        },
        {
            "type": "homework",
            "title": "The Oxygen Detective",
            "body": "",
            "format": "adventure",
            "narrative": "You are a science detective hired by the Ministry of Agriculture...",
            "tasks": [
                {
                    "id": "clue_1",
                    "instruction": "Visit any garden near your home. Count different plants.",
                    "type": "real_world",
                    "clue": "The plant count is your first code digit.",
                    "exercise_book_format": "List with sketches",
                },
                {
                    "id": "clue_2",
                    "instruction": "Calculate CO2 molecules needed for 3 glucose molecules.",
                    "type": "calculation",
                    "clue": "Your answer is the second code digit.",
                    "exercise_book_format": "Show working, circle answer",
                },
            ],
            "completion": "Combine your clues to form the case code.",
            "assessment_tip": "Check for correct equation application and real plant names.",
            "quiz": [
                {
                    "question": "What gas do plants absorb during photosynthesis?",
                    "options": ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"],
                    "correct": 1,
                    "explanation": "Plants absorb CO2 and release O2.",
                },
                {
                    "question": "Where does photosynthesis take place?",
                    "options": ["Roots", "Stem", "Leaves", "Flowers"],
                    "correct": 2,
                    "explanation": "Chloroplasts in leaves capture sunlight.",
                },
                {
                    "question": "What is the green pigment in leaves?",
                    "options": ["Melanin", "Chlorophyll", "Haemoglobin", "Carotene"],
                    "correct": 1,
                    "explanation": "Chlorophyll gives leaves their green colour.",
                },
                {
                    "question": "What is the main product of photosynthesis?",
                    "options": ["Protein", "Fat", "Glucose", "Starch"],
                    "correct": 2,
                    "explanation": "Plants produce glucose as their food.",
                },
                {
                    "question": "Which of these is NOT needed for photosynthesis?",
                    "options": ["Sunlight", "Water", "Oxygen", "Carbon dioxide"],
                    "correct": 2,
                    "explanation": "Oxygen is a product, not a reactant.",
                },
            ],
        },
        {
            "type": "teacher_notes",
            "title": "Teacher Notes",
            "body": "",
            "expected_answers": ["18 CO2 molecules for 3 glucose"],
            "common_mistakes": ["Confusing what plants absorb vs release"],
            "quick_assessment": "If a student can explain why covering a plant kills it, they understood.",
            "next_lesson_link": "Connects to cellular respiration -- the reverse process.",
            "exam_tip": "WAEC 2024 Q3 tested the balanced equation.",
            "safety_notes": None,
        },
    ],
}

SAMPLE_LESSON_JSON = json.dumps(SAMPLE_LESSON_JSON_DICT)

# --- Legacy block format (current production) ---

SAMPLE_LESSON_BLOCKS = """[BLOCK_START_OPENER]
Title: What if photosynthesis stopped tomorrow?
Summary: Ask a thought-provoking question about photosynthesis
Details: Ask students: 'If every plant stopped making food from sunlight right now, how long before we feel it?' Give them 10 seconds to guess.
[BLOCK_END]

[BLOCK_START_EXPLAIN]
Title: The Factory Inside Every Leaf
Summary: Photosynthesis explained in plain language
Details: Think of each leaf as a tiny solar-powered factory. It takes sunlight, water from the soil, and carbon dioxide from the air, and converts them into glucose (sugar) and oxygen. The equation is: 6CO2 + 6H2O -> C6H12O6 + 6O2.
[BLOCK_END]

[BLOCK_START_ACTIVITY]
Title: Photosynthesis Relay Race
Summary: Group relay race -- 12 minutes
Details: Split class into teams of 5. Each team member runs to the board and writes one step of photosynthesis in order. First team to complete all steps correctly wins.
[BLOCK_END]

[BLOCK_START_HOMEWORK]
Title: The Oxygen Detective
Summary: Detective case
Details: You are a science detective. Visit any garden and count the plants you see. Then calculate the CO2 needed for 3 glucose molecules. Write a one-paragraph detective report.
[BLOCK_END]

[BLOCK_START_TEACHER_NOTES]
Title: Teacher Notes
Summary: Quick reference for the teacher
Details: EXPECTED ANSWERS: 18 CO2 molecules. COMMON MISTAKES: Confusing absorption vs release. QUICK CHECK: Can the student explain why covering a plant kills it?
[BLOCK_END]"""

# --- Real LLM output observed in 2026-04-28 perf bench: legacy text path,
# LLM emitted Title:/Summary:/Details: triples but DROPPED the
# [BLOCK_START_X]/[BLOCK_END] outer markers. Caused silent lesson loss
# (no PDF, no homework code) until recovery parser landed.

BROKEN_LESSON_NO_MARKERS = """Title: Your Body's Secret Duplication Machine
Summary: Riddle to spark curiosity about growth
Details: "Good morning, class! Raise your hand if you've ever wondered why a tiny baby grows into a tall teenager like you. Here's a riddle: I start as one, become two, then four, eight - I'm the reason you grew from a single cell. What am I? By the end of this lesson, you'll shout the answer: Mitosis! Write that word in your books now."

Title: Unpacking Mitosis: The Cell's Cloning Process
Summary: Mitosis is how one parent cell divides to make two identical daughter cells, essential for growth, repair, and replacing old cells.
Details: "Mitosis happens in body cells - not sex cells - and keeps everything identical, like photocopying a page perfectly. Surprise: your body performs about 2 trillion mitoses every single day."

Title: Mitosis Stage Dash Relay
Summary: Groups of 5 relay race to draw and label stages -- 15 minutes
Details: "Divide into 6-12 groups of 5 students each. Student 1 runs to board, copies one stage name, returns and draws it. First group to complete all 5 labelled drawings wins."

Title: Cell Repair Detective: Solve the Knee Scrape Mystery
Summary: Detective case -- students analyze evidence from a scraped knee
Details: "You're Detective Cell, investigating a scraped knee. In your exercise book, write a 'Detective Report' (1 page): list which stage each evidence matches and why."

Title: Teacher Notes
Summary: Quick reference for the teacher
Details: "EXPECTED ANSWERS: Pro: thick chromosomes; Meta: equator line; Ana: pulling apart; Telo: two nuclei. COMMON MISTAKES: Mixing mitosis/meiosis. QUICK CHECK: Name the stage where chromosomes line up like soldiers."
"""

# --- Captured 2026-04-29 from /api/chat: SS2 Biology, "Transport in Plants
# and Animals". The 'explain' block is MISSING its 'title' field; before the
# Layer 1+2 fix this caused Pydantic to reject the whole pack, falling
# through to no lesson_pack + raw JSON in chat.

BROKEN_LESSON_MISSING_TITLE_DICT = {
    "version": "4.0",
    "meta": {
        "subject": "Biology",
        "topic": "Transport in Plants and Animals",
        "class_level": "SS2 (Form 2 KNEC)",
        "exam_board": "KNEC",
        "duration_minutes": 40,
        "language": "en",
        "bilingual": None,
    },
    "blocks": [
        {
            "type": "opener",
            "title": "The Thirsty Tree Challenge",
            "body": (
                "Imagine a giant baobab tree in the hot savanna. Its roots are deep "
                "in dry soil, but its leaves are high up, desperate for water. How "
                "does that water climb all the way up without a pump?"
            ),
            "format": "what_if",
            "duration_minutes": 2,
            "props": [],
        },
        # The bug: this 'explain' block has NO 'title' field.
        {
            "type": "explain",
            "body": (
                "Class, transport is how plants and animals move water, food, and "
                "oxygen around their bodies. In plants, xylem vessels carry water "
                "and minerals from roots up to leaves."
            ),
            "wow_fact": "A corn plant transpires 200 liters of water daily",
            "analogy": "Xylem: one-way elevator up; Phloem: delivery truck down",
            "key_terms": [
                {"term": "Xylem", "definition": "Tubes carrying water up from roots to leaves"},
                {"term": "Phloem", "definition": "Tubes moving food (sugars) from leaves to other parts"},
            ],
            "equation": None,
        },
        {
            "type": "activity",
            "title": "Transport Relay Race",
            "body": "Setup (2 min): Divide into 6 groups of 5 students each.",
            "format": "relay_race",
            "group_size": 5,
            "duration_minutes": 12,
            "materials": ["chalk", "exercise book", "pen"],
            "rules": ["One student at board at a time", "Label with key term"],
            "expected_outcome": "Students diagram and explain key transport paths",
        },
        {
            "type": "homework",
            "title": "Safari Transport Detective",
            "body": "",
            "format": "detective",
            "narrative": "You are a detective on a Kenyan safari.",
            "tasks": [
                {
                    "id": "task_1",
                    "instruction": "Draw and label xylem/phloem in acacia.",
                    "type": "observation",
                    "clue": "Clue 1: Leaves evaporate water.",
                    "exercise_book_format": "Full page sketch with labels.",
                },
            ],
            "completion": "Combine clues into a 4-sentence report.",
            "assessment_tip": "Scan for 4 tasks complete + report.",
            "quiz": [
                {
                    "question": "What carries water up in plants?",
                    "options": ["A) Phloem", "B) Xylem", "C) Blood", "D) Roots only"],
                    "correct": 1,
                    "explanation": "Xylem transports water from roots to leaves.",
                },
                {
                    "question": "Transpiration is:",
                    "options": ["A) Food movement", "B) Water evaporation from leaves", "C) Heart pumping", "D) Blood clotting"],
                    "correct": 1,
                    "explanation": "It pulls water up through xylem.",
                },
                {
                    "question": "In double circulation, blood goes to lungs for:",
                    "options": ["A) Food", "B) Oxygen", "C) Waste only", "D) Sugars"],
                    "correct": 1,
                    "explanation": "Lungs oxygenate blood before body.",
                },
                {
                    "question": "Red blood cells carry:",
                    "options": ["A) Germs", "B) Oxygen", "C) Food only", "D) Water"],
                    "correct": 1,
                    "explanation": "RBCs transport oxygen.",
                },
                {
                    "question": "Plants transport food via:",
                    "options": ["A) Blood", "B) Xylem up only", "C) Phloem down", "D) Heart"],
                    "correct": 2,
                    "explanation": "Phloem moves sugars.",
                },
            ],
        },
        {
            "type": "teacher_notes",
            "title": "Teacher Notes",
            "body": "",
            "expected_answers": ["Xylem: water up; Phloem: food down"],
            "common_mistakes": ["Confusing xylem/phloem directions"],
            "quick_assessment": "If a student can explain xylem vs phloem, they understood.",
            "next_lesson_link": "Links to Excretion.",
            "exam_tip": "KNEC KCSE: Diagrams + comparisons.",
            "safety_notes": None,
        },
    ],
}

BROKEN_LESSON_MISSING_TITLE = json.dumps(BROKEN_LESSON_MISSING_TITLE_DICT)

# --- Legacy format with OLD block names (from test_main.py) ---

SAMPLE_LESSON_OLD_NAMES = """[BLOCK_START_HOOK]
Title: The Water Cycle in Your Kitchen
Summary: You see the water cycle every time you boil water!
Details: Start by boiling a kettle and holding a cold plate above the steam.
[BLOCK_END]

[BLOCK_START_FACT]
Title: Earth Has the Same Water as the Dinosaurs
Summary: Every drop of water on Earth has been recycled for billions of years.
Details: The water cycle means no new water is created -- it just moves around.
[BLOCK_END]

[BLOCK_START_HOMEWORK]
Title: Water Detective
Summary: Story problem
Details: You are a water engineer investigating a drought.
[BLOCK_END]"""
