"""Payment abstraction and usage tracking for ClassGen.

Provider-agnostic billing layer. Supports:
- Paystack (card, USSD, bank transfer)
- Manual bank transfer with reference code verification
- Free tier with usage limits

Usage is tracked before billing -- teachers see value before hitting the paywall.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from db import supabase
from i18n import DEFAULT_CURRENCY, format_currency_short

# --- Subscription tiers ---
# Prices keyed by ISO currency code. Add new currencies here.

TIER_PRICES = {
    "free":    {"NGN": 0,    "KES": 0,    "USD": 0},
    "premium": {"NGN": 2000, "KES": 500,  "USD": 3},
    "school":  {"NGN": 5000, "KES": 1200, "USD": 7},
}

TIERS = {
    "free": {"name": "Free", "lessons_per_week": 5},
    "premium": {"name": "Premium", "lessons_per_week": -1},  # -1 = unlimited
    "school": {"name": "School", "lessons_per_week": -1, "per_seat": True},
}


def get_price(tier: str, currency: str = DEFAULT_CURRENCY) -> int:
    """Get the price for a tier in the given currency."""
    return TIER_PRICES.get(tier, TIER_PRICES["free"]).get(currency.upper(), 0)


def format_price(amount: int, currency: str = DEFAULT_CURRENCY) -> str:
    """Format an amount with the currency symbol via Babel.

    Uses short format (no decimals) for cleaner WhatsApp messages.
    """
    return format_currency_short(amount, currency)

# In-memory stores for local dev
_mem_usage: dict[str, list] = {}
_mem_subscriptions: dict[str, dict] = {}


@dataclass
class UsageCheck:
    allowed: bool
    remaining: int  # -1 = unlimited
    tier: str
    message: str = ""


# --- Usage tracking ---

def log_usage(teacher_phone: str, action: str = "lesson"):
    """Log a usage event (lesson generated, quiz created, etc.)."""
    record = {
        "teacher_phone": teacher_phone,
        "action": action,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
        _mem_usage.setdefault(teacher_phone, []).append(record)
        return
    try:
        supabase.table("usage_log").insert(record).execute()
    except Exception as e:
        print(f"Error logging usage: {e}")


def get_weekly_usage(teacher_phone: str) -> int:
    """Count lessons generated this week."""
    now = datetime.now(timezone.utc)
    # Monday of this week (safe across month boundaries)
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
    week_start_iso = week_start.isoformat()

    if not supabase:
        events = _mem_usage.get(teacher_phone, [])
        return sum(1 for e in events
                   if e.get("action") == "lesson"
                   and (e.get("created_at") or "") >= week_start_iso)
    try:
        response = (
            supabase.table("usage_log")
            .select("id", count="exact")
            .eq("teacher_phone", teacher_phone)
            .eq("action", "lesson")
            .gte("created_at", week_start_iso)
            .execute()
        )
        return response.count or 0
    except Exception as e:
        print(f"Error getting usage: {e}")
        return 0


# --- Subscriptions ---

def get_subscription(teacher_phone: str) -> dict:
    """Get a teacher's subscription tier. Defaults to free."""
    if not supabase:
        return _mem_subscriptions.get(teacher_phone, {
            "teacher_phone": teacher_phone,
            "tier": "free",
            "status": "active",
        })
    try:
        response = (
            supabase.table("subscriptions")
            .select("*")
            .eq("teacher_phone", teacher_phone)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Error getting subscription: {e}")
    return {"teacher_phone": teacher_phone, "tier": "free", "status": "active"}


def check_usage(teacher_phone: str) -> UsageCheck:
    """Check if a teacher can generate a lesson based on their tier and usage."""
    sub = get_subscription(teacher_phone)
    tier_name = sub.get("tier", "free")
    tier = TIERS.get(tier_name, TIERS["free"])
    limit = tier["lessons_per_week"]

    if limit == -1:
        return UsageCheck(allowed=True, remaining=-1, tier=tier_name)

    used = get_weekly_usage(teacher_phone)
    remaining = max(0, limit - used)

    if remaining <= 0:
        return UsageCheck(
            allowed=False, remaining=0, tier=tier_name,
            message=f"You've used all {limit} free lessons this week. "
                    f"Upgrade to Premium for unlimited lessons, or wait until next week."
        )

    return UsageCheck(allowed=True, remaining=remaining, tier=tier_name)


def save_subscription(teacher_phone: str, tier: str, payment_ref: str = "",
                      school_phone: str = "") -> bool:
    """Create or update a subscription."""
    record = {
        "teacher_phone": teacher_phone,
        "tier": tier,
        "status": "active",
        "payment_ref": payment_ref,
        "school_phone": school_phone,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if not supabase:
        _mem_subscriptions[teacher_phone] = record
        print(f"[local] Subscription {tier} for {teacher_phone}")
        return True
    try:
        supabase.table("subscriptions").upsert(
            record, on_conflict="teacher_phone"
        ).execute()
        return True
    except Exception as e:
        print(f"Error saving subscription: {e}")
        return False


# --- Payment providers ---

class PaymentProvider:
    """Base class for payment providers."""
    def create_payment_link(self, amount: int, email: str, ref: str) -> str | None:
        raise NotImplementedError

    def verify_payment(self, ref: str) -> bool:
        raise NotImplementedError


class PaystackProvider(PaymentProvider):
    """Paystack payment provider (card, USSD, bank transfer)."""
    def __init__(self):
        import os
        self.secret_key = os.environ.get("PAYSTACK_SECRET_KEY", "")

    def create_payment_link(self, amount: int, email: str, ref: str) -> str | None:
        if not self.secret_key:
            print("[local] Would create Paystack payment link")
            return None
        try:
            import httpx
            resp = httpx.post(
                "https://api.paystack.co/transaction/initialize",
                headers={"Authorization": f"Bearer {self.secret_key}"},
                json={"amount": amount * 100, "email": email, "reference": ref},
            )
            data = resp.json()
            return data.get("data", {}).get("authorization_url")
        except Exception as e:
            print(f"Paystack error: {e}")
            return None

    def verify_payment(self, ref: str) -> bool:
        if not self.secret_key:
            return False
        try:
            import httpx
            resp = httpx.get(
                f"https://api.paystack.co/transaction/verify/{ref}",
                headers={"Authorization": f"Bearer {self.secret_key}"},
            )
            data = resp.json()
            return data.get("data", {}).get("status") == "success"
        except Exception as e:
            print(f"Paystack verify error: {e}")
            return False


class BankTransferProvider(PaymentProvider):
    """Manual bank transfer with reference code verification."""
    BANK_DETAILS = {
        "bank": "Access Bank",
        "account_number": "0123456789",
        "account_name": "ClassGen Education Ltd",
    }

    def create_payment_link(self, amount: int, email: str, ref: str) -> str | None:
        # Bank transfer doesn't have a link -- return instructions
        return None

    def get_instructions(self, amount: int, ref: str, currency: str = DEFAULT_CURRENCY) -> str:
        return (
            f"*Bank Transfer*\n\n"
            f"Bank: {self.BANK_DETAILS['bank']}\n"
            f"Account: {self.BANK_DETAILS['account_number']}\n"
            f"Name: {self.BANK_DETAILS['account_name']}\n"
            f"Amount: {format_price(amount, currency)}\n"
            f"Reference: {ref}\n\n"
            f"After payment, send: confirm {ref}"
        )

    def verify_payment(self, ref: str) -> bool:
        # Manual verification -- admin confirms via dashboard
        return False
