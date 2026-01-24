"""Tests for DateTimeValidator."""

from datetime import time

import pytest

from taskdog.tui.forms.validators import DateTimeValidator


class TestDateTimeValidator:
    """Test cases for DateTimeValidator."""

    @pytest.mark.parametrize(
        "input_value,field_name,default_time,expected_valid",
        [
            # Empty/whitespace cases
            ("", "date", time(18, 30, 0), True),
            ("   ", "date", time(18, 30, 0), True),
            # Date-only cases (should apply default time)
            ("10/22", "date", time(18, 30, 0), True),
            ("2025-10-22", "date", time(18, 30, 0), True),
            # Datetime with time (should preserve time)
            ("10/22 14:30", "date", time(18, 30, 0), True),
            ("2025-12-31 23:59:59", "date", time(18, 30, 0), True),
            ("10/22 6pm", "date", time(18, 30, 0), True),
            ("10/22 00:00", "date", time(18, 30, 0), True),
            # Invalid cases
            ("invalid-date", "date", time(18, 30, 0), False),
        ],
        ids=[
            "empty_string_is_valid",
            "whitespace_only_is_valid",
            "date_only_is_valid",
            "date_with_year_is_valid",
            "datetime_with_time_is_valid",
            "full_datetime_format_is_valid",
            "with_am_pm_is_valid",
            "midnight_with_colon_is_valid",
            "invalid_date_returns_error",
        ],
    )
    def test_validate(self, input_value, field_name, default_time, expected_valid):
        """Test validation of date/time values."""
        validator = DateTimeValidator(field_name, default_time)
        result = validator.validate(input_value)

        assert result.is_valid == expected_valid

        if not expected_valid:
            assert result.failure_descriptions is not None
            assert len(result.failure_descriptions) > 0

    @pytest.mark.parametrize(
        "input_value,field_name,default_time,expected_substring",
        [
            # Empty/whitespace cases
            ("", "date", time(18, 30, 0), None),
            ("   ", "date", time(18, 30, 0), None),
            # Date-only cases (should apply default time)
            ("10/22", "date", time(18, 30, 0), "18:30:00"),
            ("10/22", "date", time(9, 30, 0), "09:30:00"),
            ("2025-10-22", "date", time(18, 30, 0), "2025-10-22 18:30:00"),
            # Datetime with time (should preserve time)
            ("10/22 14:30", "date", time(18, 30, 0), "14:30:00"),
            ("2025-12-31 23:59:59", "date", time(18, 30, 0), "2025-12-31 23:59:59"),
            ("10/22 6pm", "date", time(18, 30, 0), "18:00:00"),
            ("10/22 00:00", "date", time(18, 30, 0), "00:00:00"),
        ],
        ids=[
            "empty_string_returns_none",
            "whitespace_only_returns_none",
            "date_only_applies_default_time_18",
            "date_only_applies_default_time_9",
            "date_with_year_applies_default",
            "datetime_with_time_preserves_time",
            "full_datetime_format",
            "with_am_pm",
            "midnight_with_colon_preserves_midnight",
        ],
    )
    def test_parse(self, input_value, field_name, default_time, expected_substring):
        """Test parsing of date/time values."""
        validator = DateTimeValidator(field_name, default_time)
        result = validator.parse(input_value)

        if expected_substring is None:
            assert result is None
        else:
            assert result is not None
            assert expected_substring in result
