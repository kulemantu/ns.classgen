"""Subject-keyword -> 4-letter prefix map for mnemonic homework codes.

Teachers type lesson topics like "SS2 Biology: Photosynthesis" or
"JSS3 Maths -- Pythagoras theorem". The chat router parses these into a
(class_level, subject, topic) triple; this module turns the subject part
into a 4-letter prefix used as the leading half of a homework code
(e.g. BIOL47, MATH02).

When the subject is unknown -- empty, foreign-language, or off-curriculum --
the caller falls back to the legacy random-letters generator instead of
forcing a meaningless prefix.
"""

from __future__ import annotations

import re

# Curated to the African secondary curriculum scope (English-first). Keys are
# lowercased keywords searched as whole words against the subject string;
# values are exactly 4 uppercase ASCII letters so the resulting code stays
# the same 6-character shape as before (4 letters + 2 digits).
#
# A few entries (CRK, IRE, ICT) are abbreviations teachers actually type --
# expanding them to MATH-style 4-letter codes (CRKR, IREM, ICTC) keeps the
# shape consistent without inventing a new column width.
_SUBJECT_PREFIXES: dict[str, str] = {
    # STEM
    "biology": "BIOL",
    "bio": "BIOL",
    "chemistry": "CHEM",
    "chem": "CHEM",
    "physics": "PHYS",
    "mathematics": "MATH",
    "maths": "MATH",
    "math": "MATH",
    "further": "FMTH",  # "further maths" -> matches 'further' first
    "computer": "COMP",
    "computing": "COMP",
    "ict": "ICTC",
    "technology": "TECH",
    "agriculture": "AGRI",
    "agric": "AGRI",
    # Languages
    "english": "ENGL",
    "literature": "LITE",
    "french": "FREN",
    "swahili": "SWAH",
    "kiswahili": "SWAH",
    "yoruba": "YORU",
    "igbo": "IGBO",
    "hausa": "HAUS",
    "arabic": "ARAB",
    # Humanities
    "history": "HIST",
    "geography": "GEOG",
    "geo": "GEOG",
    "civics": "CIVI",
    "civic": "CIVI",
    "social": "SOCI",
    "government": "GOVT",
    "religious": "RELI",
    "crk": "CRKR",
    "ire": "IREM",
    # Commerce
    "economics": "ECON",
    "econ": "ECON",
    "commerce": "COMM",
    "business": "BUSN",
    "accounting": "ACCT",
    "accounts": "ACCT",
    "marketing": "MKTG",
    # Arts
    "music": "MUSI",
    "art": "ARTS",
    "drama": "DRMA",
    "physical": "PHED",  # "physical education"
    "health": "HLTH",
}


_NORMALIZE_RE = re.compile(r"[^a-z]+")


def derive_subject_prefix(subject: str) -> str:
    """Return a 4-letter prefix for ``subject`` or ``""`` when unmatched.

    Matches the first keyword in the prefix map that appears in the
    subject string. ``""`` means "fall back to random" -- callers should
    treat the empty return value as a signal, not a usable code.
    """
    if not subject:
        return ""
    normalized = _NORMALIZE_RE.sub(" ", subject.lower()).strip()
    if not normalized:
        return ""
    # Word-boundary scan in input order; first hit wins so multi-token
    # subjects like "further maths" match on the leading qualifier rather
    # than the generic suffix.
    for token in normalized.split():
        prefix = _SUBJECT_PREFIXES.get(token)
        if prefix:
            return prefix
    return ""
