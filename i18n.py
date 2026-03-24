"""Internationalization support for ClassGen.

Uses Babel for locale-aware currency, number, and date formatting.
Locale is inferred from the teacher's phone country code when available.

Supported currencies: NGN, KES, USD (add more in PHONE_LOCALES).
"""

from babel.numbers import format_currency as _babel_format_currency
from babel.dates import format_date as _babel_format_date, format_datetime as _babel_format_datetime
import datetime

# Phone country-code → (babel locale, default currency)
# Sorted longest-prefix-first at lookup time so +2547… beats +25…
PHONE_LOCALES: dict[str, tuple[str, str]] = {
    "+234": ("en_NG", "NGN"),   # Nigeria
    "+254": ("en_KE", "KES"),   # Kenya
    "+233": ("en_GH", "GHS"),   # Ghana
    "+255": ("sw_TZ", "TZS"),   # Tanzania
    "+256": ("en_UG", "UGX"),   # Uganda
    "+27":  ("en_ZA", "ZAR"),   # South Africa
    "+1":   ("en_US", "USD"),   # US / international fallback
}

# Best locale for displaying each currency's native symbol.
_CURRENCY_LOCALE: dict[str, str] = {
    "NGN": "en_NG",
    "KES": "en_KE",
    "GHS": "en_GH",
    "TZS": "sw_TZ",
    "UGX": "en_UG",
    "ZAR": "en_ZA",
    "USD": "en_US",
}

DEFAULT_LOCALE = "en_NG"
DEFAULT_CURRENCY = "NGN"

# Currencies we actively price in (subset of what Babel knows about).
SUPPORTED_CURRENCIES = {"NGN", "KES", "USD"}


def locale_from_phone(phone: str) -> tuple[str, str]:
    """Infer (locale, currency) from a phone number's country code.

    Returns (DEFAULT_LOCALE, DEFAULT_CURRENCY) if the prefix is unknown.

    >>> locale_from_phone("+2348012345678")
    ('en_NG', 'NGN')
    >>> locale_from_phone("+254712345678")
    ('en_KE', 'KES')
    """
    for prefix in sorted(PHONE_LOCALES, key=len, reverse=True):
        if phone.startswith(prefix):
            return PHONE_LOCALES[prefix]
    return DEFAULT_LOCALE, DEFAULT_CURRENCY


def format_currency(amount: float | int, currency: str,
                    locale: str | None = None) -> str:
    """Format an amount with locale-aware currency symbol and grouping.

    >>> format_currency(2000, "NGN")
    '₦2,000.00'
    >>> format_currency(500, "KES", locale="en_KE")
    'Ksh\\xa0500.00'
    """
    if locale is None:
        locale = DEFAULT_LOCALE
    return _babel_format_currency(amount, currency.upper(), locale=locale)


def format_currency_short(amount: float | int, currency: str) -> str:
    """Short format without decimals for display in WhatsApp messages.

    Uses the currency's native locale so the right symbol appears.

    >>> format_currency_short(2000, "NGN")
    '₦2,000'
    >>> format_currency_short(500, "KES")
    'Ksh500'
    >>> format_currency_short(3, "USD")
    '$3'
    """
    cur = currency.upper()
    locale = _CURRENCY_LOCALE.get(cur, DEFAULT_LOCALE)
    formatted = _babel_format_currency(amount, cur, locale=locale)
    # Strip trailing .00 for whole amounts (cleaner in chat messages)
    if isinstance(amount, int) or amount == int(amount):
        formatted = formatted.replace(".00", "")
    return formatted


def format_date(date: datetime.date, fmt: str = "medium",
                locale: str | None = None) -> str:
    """Format a date for the given locale.

    >>> import datetime
    >>> format_date(datetime.date(2026, 3, 24), locale="en_KE")
    '24 Mar 2026'
    """
    if locale is None:
        locale = DEFAULT_LOCALE
    return _babel_format_date(date, format=fmt, locale=locale)


def format_datetime(dt: datetime.datetime, fmt: str = "medium",
                    locale: str | None = None) -> str:
    """Format a datetime for the given locale."""
    if locale is None:
        locale = DEFAULT_LOCALE
    return _babel_format_datetime(dt, format=fmt, locale=locale)
