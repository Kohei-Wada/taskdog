"""Tests for StartDateTextualValidator."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from taskdog.tui.forms.validators import StartDateTextualValidator


class TestStartDateTextualValidator:
    """Test cases for StartDateTextualValidator."""

    @pytest.mark.parametrize(
        "input_value,expected_valid",
        [
            # Empty/whitespace cases (required field - should fail)
            ("", False),
            ("   ", False),
            # Date format cases
            ("2025-12-01", True),
            ("12/01", True),
            ("2025-12-01 09:00", True),
            # Relative date keywords
            ("today", True),
            ("tomorrow", True),
            ("yesterday", True),
            ("TODAY", True),
            ("Tomorrow", True),
            # Invalid cases
            ("invalid-date", False),
            ("not a date", False),
            ("asdfgh", False),
            ("あいうえお", False),
            ("!@#$%^", False),
            ("12345", False),
            ("🎉🎊", False),
            ("'; DROP TABLE tasks;--", False),
        ],
        ids=[
            "empty_string_is_invalid",
            "whitespace_only_is_invalid",
            "date_format_yyyy_mm_dd_is_valid",
            "date_format_mm_dd_is_valid",
            "date_format_with_time_is_valid",
            "today_is_valid",
            "tomorrow_is_valid",
            "yesterday_is_valid",
            "today_uppercase_is_valid",
            "tomorrow_mixed_case_is_valid",
            "invalid_date_returns_error",
            "random_text_returns_error",
            "random_word_returns_error",
            "japanese_text_returns_error",
            "special_chars_returns_error",
            "numbers_only_returns_error",
            "emoji_returns_error",
            "sql_injection_returns_error",
        ],
    )
    def test_validate(self, input_value, expected_valid):
        """Test validation of start date values."""
        validator = StartDateTextualValidator()
        result = validator.validate(input_value)

        assert result.is_valid == expected_valid

        if not expected_valid:
            assert result.failure_descriptions is not None
            assert len(result.failure_descriptions) > 0

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_today(self, mock_datetime):
        """Test parsing 'today' returns current date."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("today")

        assert result.date() == mock_now.date()

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_tomorrow(self, mock_datetime):
        """Test parsing 'tomorrow' returns next day."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("tomorrow")

        expected = mock_now.date() + timedelta(days=1)
        assert result.date() == expected

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_yesterday(self, mock_datetime):
        """Test parsing 'yesterday' returns previous day."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("yesterday")

        expected = mock_now.date() - timedelta(days=1)
        assert result.date() == expected

    def test_parse_standard_date_format(self):
        """Test parsing standard date formats."""
        validator = StartDateTextualValidator()

        result = validator.parse("2025-12-15")
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 15

    def test_normalize_date_string_preserves_non_keywords(self):
        """Test that non-keyword strings are passed through unchanged."""
        validator = StartDateTextualValidator()

        # _normalize_date_string should return the original value
        assert validator._normalize_date_string("2025-12-01") == "2025-12-01"
        assert validator._normalize_date_string("next monday") == "next monday"
