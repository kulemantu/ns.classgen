"""Curriculum topic data and suggestion engine for ClassGen.

Provides topic lists per (exam_board, subject, class) for teacher suggestions
and coverage tracking. This is an ASSIST layer -- teachers always have the
option to request any topic on demand.

Data sourced from WAEC/NECO syllabi (West Africa). KNEC/KCSE topics (East Africa) to be added.
"""

from __future__ import annotations

# Curriculum data: {exam_board: {subject: {class: [topics]}}}
# Start with WAEC SS1-SS3 core subjects. Expand over time.

TOPICS: dict[str, dict[str, dict[str, list[str]]]] = {
    "WAEC": {
        "Biology": {
            "SS1": [
                "Living and Non-living Things",
                "Classification of Living Things",
                "The Cell: Structure and Functions",
                "Cell Division: Mitosis and Meiosis",
                "Tissues and Organs",
                "Nutrition in Plants: Photosynthesis",
                "Nutrition in Animals",
                "Transport System in Plants",
                "Transport System in Animals: Circulatory System",
                "Respiration",
                "Excretion in Plants and Animals",
                "Reproduction in Plants",
                "Reproduction in Animals",
                "Growth and Development",
                "Ecology: Ecosystem and Biomes",
            ],
            "SS2": [
                "Digestive System",
                "Enzymes",
                "Photosynthesis (Advanced)",
                "Plant Respiration and Gaseous Exchange",
                "Excretory System: Kidney Structure and Function",
                "Nervous System and Coordination",
                "Hormones and Endocrine System",
                "Sense Organs: Eye and Ear",
                "Reproductive System: Human",
                "Genetics: Mendel's Laws",
                "Heredity and Variation",
                "Evolution and Natural Selection",
                "Ecology: Food Chains, Webs, and Pyramids",
                "Adaptation and Competition",
                "Conservation of Natural Resources",
            ],
            "SS3": [
                "DNA, RNA, and Protein Synthesis",
                "Genetic Engineering and Biotechnology",
                "Blood Groups and Genotypes",
                "Sex-linked Inheritance",
                "Mutation",
                "Population Studies",
                "Pollution and its Effects",
                "Disease: Causes, Transmission, Prevention",
                "Immunisation and Vaccination",
                "Aquatic and Terrestrial Habitats",
                "Microorganisms: Bacteria, Viruses, Fungi",
                "Pest and Disease Control in Agriculture",
            ],
        },
        "Mathematics": {
            "SS1": [
                "Number Bases",
                "Modular Arithmetic",
                "Indices and Logarithms",
                "Sets: Union, Intersection, Complement",
                "Simple and Compound Interest",
                "Algebraic Expressions and Factorisation",
                "Linear Equations and Inequalities",
                "Quadratic Equations",
                "Variation: Direct, Inverse, Joint",
                "Geometry: Angles and Polygons",
                "Circle Theorems",
                "Mensuration: Area and Volume",
                "Trigonometry: Sine, Cosine, Tangent",
                "Statistics: Mean, Median, Mode",
                "Probability",
            ],
            "SS2": [
                "Surds",
                "Matrices and Determinants",
                "Linear and Quadratic Graphs",
                "Coordinate Geometry: Distance, Midpoint, Gradient",
                "Simultaneous Equations (Linear and Quadratic)",
                "Arithmetic and Geometric Progressions",
                "Binary Operations",
                "Mensuration: Surface Area and Volume of Solids",
                "Trigonometry: Graphs and Identities",
                "Bearings and Distances",
                "Longitude and Latitude",
                "Statistics: Grouped Data, Cumulative Frequency",
                "Probability: Combined Events",
                "Logical Reasoning",
            ],
            "SS3": [
                "Differentiation: Basic Rules",
                "Integration: Basic Rules",
                "Application of Differentiation: Maxima and Minima",
                "Permutations and Combinations",
                "Binomial Theorem",
                "Construction and Loci",
                "Circle Geometry (Advanced)",
                "Vectors in Two Dimensions",
                "Transformation Geometry",
                "Commercial Arithmetic: Tax, Profit, Loss",
            ],
        },
        "Chemistry": {
            "SS1": [
                "Nature of Matter: Atoms, Molecules, Ions",
                "Atomic Structure and Electron Configuration",
                "Periodic Table: Groups and Periods",
                "Chemical Bonding: Ionic, Covalent, Metallic",
                "Chemical Equations and Stoichiometry",
                "States of Matter and Kinetic Theory",
                "Gas Laws: Boyle's, Charles', Combined",
                "Acids, Bases, and Salts",
                "Water: Properties, Hardness, Treatment",
                "Separation Techniques",
                "Oxidation and Reduction (Redox)",
                "Electrolysis",
            ],
            "SS2": [
                "Energy Changes in Chemical Reactions",
                "Rates of Reaction and Equilibrium",
                "Non-metals: Hydrogen, Oxygen, Carbon",
                "Halogens and Noble Gases",
                "Metals and their Compounds",
                "Iron and Steel: Extraction and Uses",
                "Organic Chemistry: Introduction and Nomenclature",
                "Alkanes, Alkenes, and Alkynes",
                "Alcohols, Carboxylic Acids, and Esters",
                "Polymers and Plastics",
                "Environmental Chemistry: Pollution",
            ],
            "SS3": [
                "Electrochemistry and Cells",
                "Nuclear Chemistry and Radioactivity",
                "Industrial Chemistry: Haber Process, Contact Process",
                "Petrochemicals and Petroleum Refining",
                "Fats, Oils, and Soaps",
                "Carbohydrates and Proteins",
                "Qualitative Analysis: Tests for Ions and Gases",
                "Quantitative Analysis: Titration Calculations",
            ],
        },
        "Physics": {
            "SS1": [
                "Measurement and Units",
                "Scalars and Vectors",
                "Motion: Speed, Velocity, Acceleration",
                "Newton's Laws of Motion",
                "Work, Energy, and Power",
                "Simple Machines and Mechanical Advantage",
                "Pressure in Solids, Liquids, and Gases",
                "Density and Relative Density",
                "Heat Energy and Temperature",
                "Thermal Expansion",
                "Heat Transfer: Conduction, Convection, Radiation",
                "Change of State and Latent Heat",
            ],
            "SS2": [
                "Waves: Properties and Types",
                "Sound Waves and Resonance",
                "Light: Reflection and Refraction",
                "Lenses and Optical Instruments",
                "Electromagnetic Spectrum",
                "Static Electricity and Electric Fields",
                "Current Electricity: Ohm's Law",
                "Resistors: Series and Parallel",
                "Electrical Energy and Power",
                "Magnetism and Magnetic Fields",
                "Electromagnetic Induction",
            ],
            "SS3": [
                "Alternating Current and Transformers",
                "Electronics: Diodes, Transistors, Logic Gates",
                "Radioactivity: Alpha, Beta, Gamma",
                "Nuclear Reactions: Fission and Fusion",
                "Photoelectric Effect",
                "Wave-Particle Duality",
                "Gravitational Fields",
                "Simple Harmonic Motion",
            ],
        },
        "English": {
            "SS1": [
                "Parts of Speech: Nouns, Verbs, Adjectives",
                "Tenses: Simple, Continuous, Perfect",
                "Sentence Structure: Simple, Compound, Complex",
                "Comprehension: Main Idea and Inference",
                "Summary Writing: Key Points and Paraphrasing",
                "Narrative Essay Writing",
                "Descriptive Essay Writing",
                "Vocabulary Development: Word Roots and Affixes",
                "Spoken English: Vowel and Consonant Sounds",
                "Letter Writing: Formal and Informal",
                "Direct and Indirect Speech",
                "Active and Passive Voice",
            ],
            "SS2": [
                "Argumentative Essay Writing",
                "Expository Essay Writing",
                "Article and Speech Writing",
                "Comprehension: Rhetorical Devices",
                "Summary Writing: Advanced Techniques",
                "Phrasal Verbs and Idioms",
                "Concord: Subject-Verb Agreement",
                "Punctuation and Mechanics",
                "Literary Appreciation: Prose",
                "Literary Appreciation: Poetry",
                "Literary Appreciation: Drama",
                "Spoken English: Stress and Intonation",
            ],
            "SS3": [
                "Report and Review Writing",
                "Critical Essay and Commentary",
                "Register and Style",
                "Logical Connectors and Cohesion",
                "Common Errors in English Usage",
                "WAEC Paper 1: Objective Test Strategies",
                "WAEC Paper 2: Essay and Letter Strategies",
                "WAEC Paper 3: Comprehension and Summary Strategies",
            ],
        },
    },
}


def get_topics(exam_board: str, subject: str, class_level: str) -> list[str]:
    """Get the topic list for a given exam board, subject, and class level."""
    board = TOPICS.get(exam_board.upper(), TOPICS.get("WAEC", {}))
    # Try exact match first, then case-insensitive
    subj = board.get(subject)
    if not subj:
        for k, v in board.items():
            if k.lower() == subject.lower():
                subj = v
                break
    if not subj:
        return []
    return subj.get(class_level.upper(), [])


def suggest_topics(
    exam_board: str, subject: str, class_level: str, covered: list[str] | None = None
) -> tuple[list[str], list[str]]:
    """Return (uncovered_topics, covered_topics) for a class.

    If covered is provided, topics already taught are separated out.
    """
    all_topics = get_topics(exam_board, subject, class_level)
    if not all_topics:
        return [], []
    if not covered:
        return all_topics, []
    covered_lower = {t.lower() for t in covered}
    uncovered = [t for t in all_topics if t.lower() not in covered_lower]
    done = [t for t in all_topics if t.lower() in covered_lower]
    return uncovered, done


def list_subjects(exam_board: str = "WAEC") -> list[str]:
    """List available subjects for an exam board."""
    return list(TOPICS.get(exam_board.upper(), TOPICS.get("WAEC", {})).keys())


def parse_class_string(class_str: str) -> tuple[str, str, str]:
    """Parse 'SS2 Biology' into (exam_board, subject, class_level).

    Defaults to WAEC. Returns ('', '', '') if unparseable.
    """
    parts = class_str.strip().split(maxsplit=1)
    if len(parts) < 2:
        return "", "", ""
    class_level = parts[0].upper()
    subject = parts[1].strip()
    return "WAEC", subject, class_level
