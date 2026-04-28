"""Internationalization support for ClassGen.

Uses Babel for locale-aware currency, number, and date formatting.
Locale is inferred from the teacher's phone country code when available.

Supported currencies: NGN, KES, USD (add more in PHONE_LOCALES).
"""

from __future__ import annotations

import datetime

from babel.dates import format_date as _babel_format_date
from babel.dates import format_datetime as _babel_format_datetime
from babel.numbers import format_currency as _babel_format_currency

# Phone country-code -> (babel locale, default currency)
# Sorted longest-prefix-first at lookup time so +2547... beats +25...
PHONE_LOCALES: dict[str, tuple[str, str]] = {
    "+234": ("en_NG", "NGN"),  # Nigeria
    "+254": ("en_KE", "KES"),  # Kenya
    "+233": ("en_GH", "GHS"),  # Ghana
    "+255": ("sw_TZ", "TZS"),  # Tanzania
    "+256": ("en_UG", "UGX"),  # Uganda
    "+27": ("en_ZA", "ZAR"),  # South Africa
    "+1": ("en_US", "USD"),  # US / international fallback
}

# Region display order for the country dropdown. Source of truth for
# both the in-memory data path and the seeded supported_countries table.
REGIONS: list[str] = [
    "East Africa",
    "West Africa",
    "Southern Africa",
    "Other",
]

# Country -> region. Drives optgroup placement in the dropdown.
# Trimmed to the 14 markets ClassGen actively supports.
COUNTRY_REGIONS: dict[str, str] = {
    "Kenya": "East Africa",
    "Rwanda": "East Africa",
    "Tanzania": "East Africa",
    "Uganda": "East Africa",
    "Cameroon": "West Africa",
    "Ghana": "West Africa",
    "Nigeria": "West Africa",
    "Botswana": "Southern Africa",
    "South Africa": "Southern Africa",
    "Zambia": "Southern Africa",
    "Zimbabwe": "Southern Africa",
    "India": "Other",
    "United Kingdom": "Other",
    "United States": "Other",
}

# Phone country-code -> country name (for WhatsApp profile auto-detection).
# Must stay a subset of COUNTRY_REGIONS — auto-detect should never assign
# a country that the dropdown can't display.
PHONE_COUNTRIES: dict[str, str] = {
    "+234": "Nigeria",
    "+254": "Kenya",
    "+233": "Ghana",
    "+255": "Tanzania",
    "+256": "Uganda",
    "+27": "South Africa",
    "+250": "Rwanda",
    "+260": "Zambia",
    "+263": "Zimbabwe",
    "+267": "Botswana",
    "+237": "Cameroon",
    "+91": "India",
    "+44": "United Kingdom",
    "+1": "United States",
}

# All supported countries for web dropdown — derived from COUNTRY_REGIONS.
SUPPORTED_COUNTRIES: list[str] = sorted(COUNTRY_REGIONS.keys())

# Flag emoji per supported country. Pure presentation — never stored in
# DB or sent to LLM.
COUNTRY_FLAGS: dict[str, str] = {
    "Botswana": "\U0001f1e7\U0001f1fc",
    "Cameroon": "\U0001f1e8\U0001f1f2",
    "Ghana": "\U0001f1ec\U0001f1ed",
    "India": "\U0001f1ee\U0001f1f3",
    "Kenya": "\U0001f1f0\U0001f1ea",
    "Nigeria": "\U0001f1f3\U0001f1ec",
    "Rwanda": "\U0001f1f7\U0001f1fc",
    "South Africa": "\U0001f1ff\U0001f1e6",
    "Tanzania": "\U0001f1f9\U0001f1ff",
    "Uganda": "\U0001f1fa\U0001f1ec",
    "United Kingdom": "\U0001f1ec\U0001f1e7",
    "United States": "\U0001f1fa\U0001f1f8",
    "Zambia": "\U0001f1ff\U0001f1f2",
    "Zimbabwe": "\U0001f1ff\U0001f1fc",
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


def country_from_phone(phone: str) -> str:
    """Infer country name from a phone number's country code.

    Returns empty string if the prefix is unknown.

    >>> country_from_phone("+2348012345678")
    'Nigeria'
    >>> country_from_phone("whatsapp:+254712345678")
    'Kenya'
    >>> country_from_phone("+9999999")
    ''
    """
    # Strip whatsapp: prefix if present
    clean = phone.replace("whatsapp:", "")
    for prefix in sorted(PHONE_COUNTRIES, key=len, reverse=True):
        if clean.startswith(prefix):
            return PHONE_COUNTRIES[prefix]
    return ""


def format_currency(amount: float | int, currency: str, locale: str | None = None) -> str:
    """Format an amount with locale-aware currency symbol and grouping.

    >>> format_currency(2000, "NGN")
    '\u20a62,000.00'
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
    '\u20a62,000'
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


def format_date(date: datetime.date, fmt: str = "medium", locale: str | None = None) -> str:
    """Format a date for the given locale.

    >>> import datetime
    >>> format_date(datetime.date(2026, 3, 24), locale="en_KE")
    '24 Mar 2026'
    """
    if locale is None:
        locale = DEFAULT_LOCALE
    return _babel_format_date(date, format=fmt, locale=locale)


def format_datetime(dt: datetime.datetime, fmt: str = "medium", locale: str | None = None) -> str:
    """Format a datetime for the given locale."""
    if locale is None:
        locale = DEFAULT_LOCALE
    return _babel_format_datetime(dt, format=fmt, locale=locale)
