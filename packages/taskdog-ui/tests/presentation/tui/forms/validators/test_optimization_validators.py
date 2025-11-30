"""Tests for StartDateTextualValidator."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from parameterized import parameterized

from taskdog.tui.forms.validators import StartDateTextualValidator


class TestStartDateTextualValidator(unittest.TestCase):
    """Test cases for StartDateTextualValidator."""

    @parameterized.expand(
        [
            # Empty/whitespace cases (required field - should fail)
            ("empty_string_is_invalid", "", False),
            ("whitespace_only_is_invalid", "   ", False),
            # Date format cases
            ("date_format_yyyy_mm_dd_is_valid", "2025-12-01", True),
            ("date_format_mm_dd_is_valid", "12/01", True),
            ("date_format_with_time_is_valid", "2025-12-01 09:00", True),
            # Relative date keywords
            ("today_is_valid", "today", True),
            ("tomorrow_is_valid", "tomorrow", True),
            ("yesterday_is_valid", "yesterday", True),
            ("today_uppercase_is_valid", "TODAY", True),
            ("tomorrow_mixed_case_is_valid", "Tomorrow", True),
            # Invalid cases
            ("invalid_date_returns_error", "invalid-date", False),
            ("random_text_returns_error", "not a date", False),
            ("random_word_returns_error", "asdfgh", False),
            ("japanese_text_returns_error", "あいうえお", False),
            ("special_chars_returns_error", "!@#$%^", False),
            ("numbers_only_returns_error", "12345", False),
            ("emoji_returns_error", "🎉🎊", False),
            ("sql_injection_returns_error", "'; DROP TABLE tasks;--", False),
        ]
    )
    def test_validate(self, scenario, input_value, expected_valid):
        """Test validation of start date values."""
        validator = StartDateTextualValidator()
        result = validator.validate(input_value)

        self.assertEqual(result.is_valid, expected_valid, f"Failed for: {scenario}")

        if not expected_valid:
            self.assertIsNotNone(result.failure_descriptions)
            self.assertTrue(len(result.failure_descriptions) > 0)

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_today(self, mock_datetime):
        """Test parsing 'today' returns current date."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("today")

        self.assertEqual(result.date(), mock_now.date())

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_tomorrow(self, mock_datetime):
        """Test parsing 'tomorrow' returns next day."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("tomorrow")

        expected = mock_now.date() + timedelta(days=1)
        self.assertEqual(result.date(), expected)

    @patch("taskdog.tui.forms.validators.optimization_validators.datetime")
    def test_parse_yesterday(self, mock_datetime):
        """Test parsing 'yesterday' returns previous day."""
        mock_now = datetime(2025, 12, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        validator = StartDateTextualValidator()
        result = validator.parse("yesterday")

        expected = mock_now.date() - timedelta(days=1)
        self.assertEqual(result.date(), expected)

    def test_parse_standard_date_format(self):
        """Test parsing standard date formats."""
        validator = StartDateTextualValidator()

        result = validator.parse("2025-12-15")
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 15)

    def test_normalize_date_string_preserves_non_keywords(self):
        """Test that non-keyword strings are passed through unchanged."""
        validator = StartDateTextualValidator()

        # _normalize_date_string should return the original value
        self.assertEqual(validator._normalize_date_string("2025-12-01"), "2025-12-01")
        self.assertEqual(validator._normalize_date_string("next monday"), "next monday")


if __name__ == "__main__":
    unittest.main()
