"""Billing tier data and usage models for ClassGen.

Pure data — no I/O, no Supabase, no imports of the data layer.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Subscription tiers ---
# Prices keyed by ISO currency code. Add new currencies here.

TIER_PRICES = {
    "free": {"NGN": 0, "KES": 0, "USD": 0},
    "premium": {"NGN": 2000, "KES": 500, "USD": 3},
    "school": {"NGN": 5000, "KES": 1200, "USD": 7},
}

TIERS = {
    "free": {"name": "Free", "lessons_per_week": 5},
    "premium": {"name": "Premium", "lessons_per_week": -1},  # -1 = unlimited
    "school": {"name": "School", "lessons_per_week": -1, "per_seat": True},
}

TIER_LIMITS = {tier: info["lessons_per_week"] for tier, info in TIERS.items()}


@dataclass
class UsageCheck:
    allowed: bool
    remaining: int  # -1 = unlimited
    tier: str
    message: str = ""
