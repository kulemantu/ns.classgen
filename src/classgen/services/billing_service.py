"""Payment abstraction and usage tracking for ClassGen.

Provider-agnostic billing layer. Supports:
- Paystack (card, USSD, bank transfer)
- Manual bank transfer with reference code verification
- Free tier with usage limits

Usage is tracked before billing -- teachers see value before hitting the paywall.
"""

from __future__ import annotations

from classgen.core.billing import TIERS, UsageCheck
from classgen.data.subscriptions import (
    get_subscription,
    get_weekly_usage,
)
from classgen.i18n import DEFAULT_CURRENCY, format_currency_short


def get_price(tier: str, currency: str = DEFAULT_CURRENCY) -> int:
    """Get the price for a tier in the given currency."""
    from classgen.core.billing import TIER_PRICES

    return TIER_PRICES.get(tier, TIER_PRICES["free"]).get(currency.upper(), 0)


def format_price(amount: int, currency: str = DEFAULT_CURRENCY) -> str:
    """Format an amount with the currency symbol via Babel.

    Uses short format (no decimals) for cleaner WhatsApp messages.
    """
    return format_currency_short(amount, currency)


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
            allowed=False,
            remaining=0,
            tier=tier_name,
            message=f"You've used all {limit} free lessons this week. "
            f"Upgrade to Premium for unlimited lessons, or wait until next week.",
        )

    return UsageCheck(allowed=True, remaining=remaining, tier=tier_name)


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
