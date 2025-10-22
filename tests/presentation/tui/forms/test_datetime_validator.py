"""Tests for DateTimeValidatorTUI and related validators."""

import unittest

from presentation.tui.forms.validators import (
    DateTimeValidatorTUI,
    DeadlineValidator,
    PlannedEndValidator,
    PlannedStartValidator,
)


class TestDateTimeValidatorTUI(unittest.TestCase):
    """Test cases for DateTimeValidatorTUI."""

    def test_validate_with_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = DateTimeValidatorTUI.validate("", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.value)
        self.assertEqual(result.error_message, "")

    def test_validate_with_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = DateTimeValidatorTUI.validate("   ", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.value)

    def test_validate_date_only_applies_default_hour(self):
        """Test that date-only input (10/22) gets default hour 18:00."""
        result = DateTimeValidatorTUI.validate("10/22", "date", 18)
        self.assertTrue(result.is_valid)
        # Should be current year, 10/22 18:00:00
        self.assertIsNotNone(result.value)
        self.assertIn("10-22 18:00:00", result.value)

    def test_validate_date_only_with_custom_default_hour(self):
        """Test that date-only input gets custom default hour."""
        result = DateTimeValidatorTUI.validate("10/22", "date", 9)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        self.assertIn("10-22 09:00:00", result.value)

    def test_validate_datetime_with_time_preserves_time(self):
        """Test that datetime with time component preserves the time."""
        result = DateTimeValidatorTUI.validate("10/22 14:30", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        # Should preserve 14:30, not apply default_hour
        self.assertIn("10-22 14:30:00", result.value)

    def test_validate_full_datetime_format(self):
        """Test validation with full datetime format."""
        result = DateTimeValidatorTUI.validate("2025-12-31 23:59:59", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, "2025-12-31 23:59:59")

    def test_validate_date_with_year(self):
        """Test date with year applies default hour."""
        result = DateTimeValidatorTUI.validate("2025-10-22", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, "2025-10-22 18:00:00")

    def test_validate_with_am_pm(self):
        """Test that AM/PM format works."""
        result = DateTimeValidatorTUI.validate("10/22 6pm", "date", 18)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        # Should have 18:00:00 (6pm) from input
        self.assertIn("18:00:00", result.value)

    def test_validate_invalid_date_returns_error(self):
        """Test validation fails with invalid date."""
        result = DateTimeValidatorTUI.validate("invalid-date", "date", 18)
        self.assertFalse(result.is_valid)
        self.assertIn("Invalid", result.error_message)
        self.assertIsNone(result.value)

    def test_validate_midnight_with_colon_preserves_midnight(self):
        """Test that explicit midnight (00:00) is preserved."""
        result = DateTimeValidatorTUI.validate("10/22 00:00", "date", 18)
        self.assertTrue(result.is_valid)
        # Should preserve 00:00 because ":" was present
        self.assertIn("00:00:00", result.value)


class TestDeadlineValidator(unittest.TestCase):
    """Test cases for DeadlineValidator."""

    def test_validate_date_only_uses_default_end_hour(self):
        """Test that deadline without time uses default end hour (18)."""
        result = DeadlineValidator.validate("10/22", 18)
        self.assertTrue(result.is_valid)
        self.assertIn("18:00:00", result.value)

    def test_validate_with_custom_default_hour(self):
        """Test that custom default hour is applied."""
        result = DeadlineValidator.validate("10/22", 20)
        self.assertTrue(result.is_valid)
        self.assertIn("20:00:00", result.value)

    def test_validate_with_time_preserves_time(self):
        """Test that deadline with time preserves it."""
        result = DeadlineValidator.validate("10/22 14:00", 18)
        self.assertTrue(result.is_valid)
        self.assertIn("14:00:00", result.value)


class TestPlannedStartValidator(unittest.TestCase):
    """Test cases for PlannedStartValidator."""

    def test_validate_date_only_uses_default_start_hour(self):
        """Test that planned start without time uses default start hour (9)."""
        result = PlannedStartValidator.validate("10/22", 9)
        self.assertTrue(result.is_valid)
        self.assertIn("09:00:00", result.value)

    def test_validate_with_custom_default_hour(self):
        """Test that custom default hour is applied."""
        result = PlannedStartValidator.validate("10/22", 8)
        self.assertTrue(result.is_valid)
        self.assertIn("08:00:00", result.value)

    def test_validate_with_time_preserves_time(self):
        """Test that planned start with time preserves it."""
        result = PlannedStartValidator.validate("10/22 10:00", 9)
        self.assertTrue(result.is_valid)
        self.assertIn("10:00:00", result.value)


class TestPlannedEndValidator(unittest.TestCase):
    """Test cases for PlannedEndValidator."""

    def test_validate_date_only_uses_default_end_hour(self):
        """Test that planned end without time uses default end hour (18)."""
        result = PlannedEndValidator.validate("10/22", 18)
        self.assertTrue(result.is_valid)
        self.assertIn("18:00:00", result.value)

    def test_validate_with_custom_default_hour(self):
        """Test that custom default hour is applied."""
        result = PlannedEndValidator.validate("10/22", 17)
        self.assertTrue(result.is_valid)
        self.assertIn("17:00:00", result.value)

    def test_validate_with_time_preserves_time(self):
        """Test that planned end with time preserves it."""
        result = PlannedEndValidator.validate("10/22 16:00", 18)
        self.assertTrue(result.is_valid)
        self.assertIn("16:00:00", result.value)


if __name__ == "__main__":
    unittest.main()
