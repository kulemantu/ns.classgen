"""Read-only access to the supported_countries reference table.

In prod the rows live in Postgres (seeded by migration 006). When the
Supabase client is unavailable (tests, local dev without DB) we derive
the same shape from the constants in ``classgen.i18n`` — the test suite
asserts the two stay in sync.
"""

from __future__ import annotations

from typing import cast

from classgen.i18n import COUNTRY_FLAGS, COUNTRY_REGIONS, REGIONS, SUPPORTED_COUNTRIES

from .client import supabase


def list_grouped() -> list[dict]:
    """Return countries grouped by region in display order.

    Shape: ``[{"region": "East Africa", "countries": [{"name", "flag"}, ...]}]``
    Empty regions are omitted.
    """
    if not supabase:
        return _from_constants()

    try:
        response = (
            supabase.table("supported_countries")
            .select("name,flag,region,sort_order")
            .order("sort_order")
            .execute()
        )
        rows = cast(list[dict], response.data or [])
    except Exception:
        return _from_constants()

    if not rows:
        return _from_constants()

    grouped: dict[str, list[dict]] = {region: [] for region in REGIONS}
    for row in rows:
        region = str(row["region"])
        grouped.setdefault(region, []).append(
            {"name": str(row["name"]), "flag": str(row["flag"])}
        )
    return [{"region": r, "countries": grouped[r]} for r in REGIONS if grouped.get(r)]


def _from_constants() -> list[dict]:
    grouped: dict[str, list[dict]] = {region: [] for region in REGIONS}
    for country in SUPPORTED_COUNTRIES:
        region = COUNTRY_REGIONS[country]
        grouped[region].append({"name": country, "flag": COUNTRY_FLAGS[country]})
    return [{"region": r, "countries": grouped[r]} for r in REGIONS if grouped[r]]
