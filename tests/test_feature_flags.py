"""Tests for classgen.core.feature_flags — env-var-driven feature flags."""

import os
from unittest.mock import patch

from classgen.core.feature_flags import FeatureFlags


class TestFeatureFlags:
    def setup_method(self):
        self.flags = FeatureFlags()

    def test_defaults_off(self):
        """All flags off when env vars are unset."""
        with patch.dict(os.environ, {}, clear=True):
            assert not self.flags.structured_output
            assert not self.flags.sse_streaming
            assert not self.flags.json_response_format
            assert not self.flags.embedded_quiz

    def test_enabled_true(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}):
            assert self.flags.structured_output

    def test_enabled_1(self):
        with patch.dict(os.environ, {"FF_SSE_STREAMING": "1"}):
            assert self.flags.sse_streaming

    def test_enabled_yes(self):
        with patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "yes"}):
            assert self.flags.json_response_format

    def test_enabled_true_uppercase(self):
        with patch.dict(os.environ, {"FF_EMBEDDED_QUIZ": "TRUE"}):
            assert self.flags.embedded_quiz

    def test_disabled_empty(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": ""}):
            assert not self.flags.structured_output

    def test_disabled_false(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "false"}):
            assert not self.flags.structured_output

    def test_disabled_no(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "no"}):
            assert not self.flags.structured_output

    def test_disabled_random_string(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "maybe"}):
            assert not self.flags.structured_output

    def test_flags_compose_independently(self):
        """One flag on does not affect others."""
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True):
            assert self.flags.structured_output
            assert not self.flags.sse_streaming
            assert not self.flags.json_response_format
            assert not self.flags.embedded_quiz


class TestEffectiveFlags:
    """Effective flags resolve the dependency hierarchy."""

    def setup_method(self):
        self.flags = FeatureFlags()

    # --- effective_sse_streaming ---

    def test_sse_needs_structured_output(self):
        """SSE alone is not effective without structured_output."""
        with patch.dict(os.environ, {"FF_SSE_STREAMING": "true"}, clear=True):
            assert self.flags.sse_streaming is True  # raw flag is on
            assert self.flags.effective_sse_streaming is False  # effective is off

    def test_sse_with_structured_output(self):
        with patch.dict(
            os.environ,
            {
                "FF_SSE_STREAMING": "true",
                "FF_STRUCTURED_OUTPUT": "true",
            },
            clear=True,
        ):
            assert self.flags.effective_sse_streaming is True

    def test_structured_output_alone_no_sse(self):
        with patch.dict(os.environ, {"FF_STRUCTURED_OUTPUT": "true"}, clear=True):
            assert self.flags.effective_sse_streaming is False

    # --- effective_embedded_quiz ---

    def test_embedded_quiz_needs_structured_output(self):
        """Embedded quiz alone is not effective without structured_output."""
        with patch.dict(os.environ, {"FF_EMBEDDED_QUIZ": "true"}, clear=True):
            assert self.flags.embedded_quiz is True
            assert self.flags.effective_embedded_quiz is False

    def test_embedded_quiz_with_structured_output(self):
        with patch.dict(
            os.environ,
            {
                "FF_EMBEDDED_QUIZ": "true",
                "FF_STRUCTURED_OUTPUT": "true",
            },
            clear=True,
        ):
            assert self.flags.effective_embedded_quiz is True

    # --- effective_json_response_format ---

    def test_json_format_needs_structured_output(self):
        with patch.dict(os.environ, {"FF_JSON_RESPONSE_FORMAT": "true"}, clear=True):
            assert self.flags.json_response_format is True
            assert self.flags.effective_json_response_format is False

    def test_json_format_with_structured_output(self):
        with patch.dict(
            os.environ,
            {
                "FF_JSON_RESPONSE_FORMAT": "true",
                "FF_STRUCTURED_OUTPUT": "true",
            },
            clear=True,
        ):
            assert self.flags.effective_json_response_format is True

    # --- All defaults off ---

    def test_all_effective_flags_off_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            assert self.flags.effective_sse_streaming is False
            assert self.flags.effective_embedded_quiz is False
            assert self.flags.effective_json_response_format is False

    # --- All on ---

    def test_all_effective_flags_on_when_all_enabled(self):
        with patch.dict(
            os.environ,
            {
                "FF_STRUCTURED_OUTPUT": "true",
                "FF_SSE_STREAMING": "true",
                "FF_JSON_RESPONSE_FORMAT": "true",
                "FF_EMBEDDED_QUIZ": "true",
            },
            clear=True,
        ):
            assert self.flags.effective_sse_streaming is True
            assert self.flags.effective_embedded_quiz is True
            assert self.flags.effective_json_response_format is True
