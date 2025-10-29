"""Tests for DateTimeValidator."""

import unittest

from presentation.tui.forms.validators import DateTimeValidator


class TestDateTimeValidator(unittest.TestCase):
    """Test cases for DateTimeValidator."""

    def test_validate_with_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = DateTimeValidator.validate("", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.value)
        self.assertEqual(result.error_message, "")

    def test_validate_with_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = DateTimeValidator.validate("   ", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.value)

    def test_validate_date_only_applies_default_hour(self):
        """Test that date-only input (10/22) gets default hour 18:00."""
        result = DateTimeValidator.validate("10/22", "date", 18)
        self.assertTrue(result.is_valid)
        # Should be current year, 10/22 18:00:00
        self.assertIsNotNone(result.value)
        self.assertIn("10-22 18:00:00", result.value)

    def test_validate_date_only_with_custom_default_hour(self):
        """Test that date-only input gets custom default hour."""
        result = DateTimeValidator.validate("10/22", "date", 9)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        self.assertIn("10-22 09:00:00", result.value)

    def test_validate_datetime_with_time_preserves_time(self):
        """Test that datetime with time component preserves the time."""
        result = DateTimeValidator.validate("10/22 14:30", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        # Should preserve 14:30, not apply default_hour
        self.assertIn("10-22 14:30:00", result.value)

    def test_validate_full_datetime_format(self):
        """Test validation with full datetime format."""
        result = DateTimeValidator.validate("2025-12-31 23:59:59", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, "2025-12-31 23:59:59")

    def test_validate_date_with_year(self):
        """Test date with year applies default hour."""
        result = DateTimeValidator.validate("2025-10-22", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, "2025-10-22 18:00:00")

    def test_validate_with_am_pm(self):
        """Test that AM/PM format works."""
        result = DateTimeValidator.validate("10/22 6pm", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        # Should have 18:00:00 (6pm) from input
        self.assertIn("18:00:00", result.value)

    def test_validate_invalid_date_returns_error(self):
        """Test validation fails with invalid date."""
        result = DateTimeValidator.validate("invalid-date", "date", 18)
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_midnight_with_colon_preserves_midnight(self):
        """Test that explicit midnight (00:00) is preserved."""
        result = DateTimeValidator.validate("10/22 00:00", "date", 18)
        self.assertTrue(result.is_valid)
        # Should preserve 00:00 because ":" was present
        self.assertIn("00:00:00", result.value)


if __name__ == "__main__":
    unittest.main()
