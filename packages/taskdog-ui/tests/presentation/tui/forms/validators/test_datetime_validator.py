"""Tests for DateTimeValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import DateTimeValidator


class TestDateTimeValidator(unittest.TestCase):
    """Test cases for DateTimeValidator."""

    @parameterized.expand(
        [
            # Empty/whitespace cases
            ("empty_string_is_valid", "", "date", 18, True),
            ("whitespace_only_is_valid", "   ", "date", 18, True),
            # Date-only cases (should apply default hour)
            ("date_only_is_valid", "10/22", "date", 18, True),
            ("date_with_year_is_valid", "2025-10-22", "date", 18, True),
            # Datetime with time (should preserve time)
            ("datetime_with_time_is_valid", "10/22 14:30", "date", 18, True),
            ("full_datetime_format_is_valid", "2025-12-31 23:59:59", "date", 18, True),
            ("with_am_pm_is_valid", "10/22 6pm", "date", 18, True),
            ("midnight_with_colon_is_valid", "10/22 00:00", "date", 18, True),
            # Invalid cases
            ("invalid_date_returns_error", "invalid-date", "date", 18, False),
        ]
    )
    def test_validate(
        self,
        scenario,
        input_value,
        field_name,
        default_hour,
        expected_valid,
    ):
        """Test validation of date/time values."""
        validator = DateTimeValidator(field_name, default_hour)
        result = validator.validate(input_value)

        self.assertEqual(result.is_valid, expected_valid)

        if not expected_valid:
            self.assertIsNotNone(result.failure_descriptions)
            self.assertTrue(len(result.failure_descriptions) > 0)

    @parameterized.expand(
        [
            # Empty/whitespace cases
            ("empty_string_returns_none", "", "date", 18, None),
            ("whitespace_only_returns_none", "   ", "date", 18, None),
            # Date-only cases (should apply default hour)
            ("date_only_applies_default_hour_18", "10/22", "date", 18, "18:00:00"),
            ("date_only_applies_default_hour_9", "10/22", "date", 9, "09:00:00"),
            (
                "date_with_year_applies_default",
                "2025-10-22",
                "date",
                18,
                "2025-10-22 18:00:00",
            ),
            # Datetime with time (should preserve time)
            (
                "datetime_with_time_preserves_time",
                "10/22 14:30",
                "date",
                18,
                "14:30:00",
            ),
            (
                "full_datetime_format",
                "2025-12-31 23:59:59",
                "date",
                18,
                "2025-12-31 23:59:59",
            ),
            ("with_am_pm", "10/22 6pm", "date", 18, "18:00:00"),
            (
                "midnight_with_colon_preserves_midnight",
                "10/22 00:00",
                "date",
                18,
                "00:00:00",
            ),
        ]
    )
    def test_parse(
        self,
        scenario,
        input_value,
        field_name,
        default_hour,
        expected_substring,
    ):
        """Test parsing of date/time values."""
        validator = DateTimeValidator(field_name, default_hour)
        result = validator.parse(input_value)

        if expected_substring is None:
            self.assertIsNone(result)
        else:
            self.assertIsNotNone(result)
            self.assertIn(expected_substring, result)


if __name__ == "__main__":
    unittest.main()
