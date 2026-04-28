"""Onboarding content for ClassGen — shared across web and WhatsApp channels.

Single source of truth for all intro copy. The web frontend reads this
via the ``/api/onboarding`` endpoint. The WhatsApp webhook uses it
to build the welcome message for new users.
"""

from __future__ import annotations

ONBOARDING = {
    "brand": "ClassGen",
    "tagline": "Your Teaching assistant that gives you super powers ",
    "subtitle": ("Ready-to-teach lesson packs for your classroom \u2014 in seconds"),
    "slides": [
        {
            "heading": "Type a topic. Get a lesson pack.",
            "body": (
                "Send any topic and get a structured lesson:"
                " opener hook, core concept, classroom activity,"
                " exercise-book homework, and teacher notes."
            ),
            "examples": [
                "\U0001f1f3\U0001f1ec · SS2, Nigeria, Biology, Photosynthesis, 40 mins",
                "\U0001f1f0\U0001f1ea · Form 3, Wave Motion, Physics, Kenya, 1 hour",
                (
                    "\U0001f1f7\U0001f1fc · History, Rwanda, Senior 4,"
                    " Colonial Rule in East Africa, 45 mins"
                ),
                "\U0001f1ee\U0001f1f3 · Class 10, India, Quadratic Equations, Maths, 1h 20 mins",
            ],
        },
        {
            "heading": "Everything your students need",
            "features": [
                "Download & print lesson plans as PDF",
                "Homework codes with auto-graded quizzes",
                "Works on WhatsApp too \u2014 just send a message",
            ],
        },
    ],
    "cta": "Accept & Start Teaching",
    "skip": "Skip",
    "terms_url": "/terms",
    "terms_text": "By continuing you agree to our Terms & Privacy Policy",
}


def whatsapp_welcome(base_url: str) -> str:
    """Build the WhatsApp welcome message from the shared config."""
    o = ONBOARDING
    features = o["slides"][1]["features"]
    return (
        f"*Welcome to {o['brand']}!* \U0001f30d\n\n"
        f"{o['tagline']} \u2014 {o['subtitle']}\n\n"
        f"\U0001f4dd {features[0]}\n"
        f"\U0001f4cb {features[1]}\n"
        f"\U0001f4f1 {features[2]}\n\n"
        f"{o['terms_text']}: {base_url}{o['terms_url']}\n\n"
        "Reply *YES* to get started, or *HELP* for all commands."
    )
