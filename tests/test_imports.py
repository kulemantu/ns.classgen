"""Verify every src/classgen/ module is importable.

This catches broken imports, circular dependencies, and missing __init__.py
files early — before any logic tests run.
"""

import importlib
import pkgutil

import classgen


def _all_module_names():
    """Walk the classgen package and yield all fully-qualified module names."""
    for info in pkgutil.walk_packages(classgen.__path__, prefix="classgen."):
        yield info.name


def test_all_modules_importable():
    """Every module under src/classgen/ should import without error."""
    failures = []
    for name in _all_module_names():
        try:
            importlib.import_module(name)
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    assert failures == [], "Failed imports:\n" + "\n".join(failures)


def test_key_public_api():
    """Smoke-test the most important public imports."""
    from classgen.api.app import app  # noqa: F401
    from classgen.commands.router import CommandResult, handle_command  # noqa: F401
    from classgen.content.curriculum import suggest_topics  # noqa: F401
    from classgen.content.pdf_generator import generate_pdf_from_markdown  # noqa: F401
    from classgen.core.billing import TIERS, UsageCheck  # noqa: F401
    from classgen.data import log_session, save_teacher  # noqa: F401
    from classgen.data.client import supabase  # noqa: F401
    from classgen.i18n import format_currency  # noqa: F401
    from classgen.services.billing_service import check_usage  # noqa: F401
    from classgen.services.llm import call_openrouter  # noqa: F401
