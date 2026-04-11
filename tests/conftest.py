"""Shared test fixtures.

Auto-patches is_onboarded to return True so existing webhook tests
don't hit the onboarding guard. Tests that specifically test onboarding
behavior should mock is_onboarded themselves.
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _bypass_onboarding():
    """Skip onboarding check in all tests by default."""
    with patch("classgen.api.webhook.is_onboarded", return_value=True):
        yield
