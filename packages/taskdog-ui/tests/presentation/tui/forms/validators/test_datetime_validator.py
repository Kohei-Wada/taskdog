"""Tests for DateTimeValidator."""

import unittest

from parameterized import parameterized

from taskdog.tui.forms.validators import DateTimeValidator


class TestDateTimeValidator(unittest.TestCase):
    """Test cases for DateTimeValidator."""

    @parameterized.expand(
        [
            # Empty/whitespace cases
            ("empty_string_returns_none", "", "date", 18, True, None, ""),
            ("whitespace_only_returns_none", "   ", "date", 18, True, None, ""),
            # Date-only cases (should apply default hour)
            (
                "date_only_applies_default_hour_18",
                "10/22",
                "date",
                18,
                True,
                "18:00:00",
                "",
            ),
            (
                "date_only_applies_default_hour_9",
                "10/22",
                "date",
                9,
                True,
                "09:00:00",
                "",
            ),
            (
                "date_with_year_applies_default",
                "2025-10-22",
                "date",
                18,
                True,
                "2025-10-22 18:00:00",
                "",
            ),
            # Datetime with time (should preserve time)
            (
                "datetime_with_time_preserves_time",
                "10/22 14:30",
                "date",
                18,
                True,
                "14:30:00",
                "",
            ),
            (
                "full_datetime_format",
                "2025-12-31 23:59:59",
                "date",
                18,
                True,
                "2025-12-31 23:59:59",
                "",
            ),
            ("with_am_pm", "10/22 6pm", "date", 18, True, "18:00:00", ""),
            (
                "midnight_with_colon_preserves_midnight",
                "10/22 00:00",
                "date",
                18,
                True,
                "00:00:00",
                "",
            ),
            # Invalid cases
            (
                "invalid_date_returns_error",
                "invalid-date",
                "date",
                18,
                False,
                None,
                "Invalid",
            ),
        ]
    )
    def test_validate(
        self,
        scenario,
        input_value,
        field_name,
        default_hour,
        expected_valid,
        expected_substring,
        error_substring,
    ):
        """Test validation of date/time values."""
        result = DateTimeValidator.validate(input_value, field_name, default_hour)

        self.assertEqual(result.is_valid, expected_valid)

        if expected_valid:
            if expected_substring is None:
                self.assertIsNone(result.value)
            else:
                self.assertIsNotNone(result.value)
                self.assertIn(expected_substring, result.value)
            self.assertEqual(result.error_message, "")
        else:
            self.assertIsNone(result.value)
            if error_substring:
                self.assertIn(error_substring, result.error_message)


if __name__ == "__main__":
    unittest.main()
