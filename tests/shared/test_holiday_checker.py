"""Tests for HolidayChecker utility."""

import unittest
from datetime import date

from shared.utils.holiday_checker import HolidayChecker


class TestHolidayCheckerJapan(unittest.TestCase):
    """Test cases for HolidayChecker with Japanese holidays."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = HolidayChecker("JP")

    def test_new_years_day(self):
        """Test that New Year's Day is recognized as a holiday."""
        self.assertTrue(self.checker.is_holiday(date(2025, 1, 1)))

    def test_golden_week_showa_day(self):
        """Test that Showa Day (April 29) is recognized."""
        self.assertTrue(self.checker.is_holiday(date(2025, 4, 29)))

    def test_golden_week_constitution_day(self):
        """Test that Constitution Day (May 3) is recognized."""
        self.assertTrue(self.checker.is_holiday(date(2025, 5, 3)))

    def test_golden_week_greenery_day(self):
        """Test that Greenery Day (May 4) is recognized."""
        self.assertTrue(self.checker.is_holiday(date(2025, 5, 4)))

    def test_golden_week_childrens_day(self):
        """Test that Children's Day (May 5) is recognized."""
        self.assertTrue(self.checker.is_holiday(date(2025, 5, 5)))

    def test_regular_weekday_not_holiday(self):
        """Test that a regular weekday is not a holiday."""
        self.assertFalse(self.checker.is_holiday(date(2025, 1, 7)))  # Tuesday

    def test_regular_weekend_not_holiday(self):
        """Test that a regular weekend is not a holiday."""
        self.assertFalse(self.checker.is_holiday(date(2025, 1, 4)))  # Saturday

    def test_get_holiday_name(self):
        """Test that holiday names are retrieved correctly."""
        name = self.checker.get_holiday_name(date(2025, 1, 1))
        self.assertIsNotNone(name)
        # Holiday name should contain something (varies by language)
        self.assertGreater(len(name), 0)

    def test_get_holiday_name_non_holiday(self):
        """Test that non-holidays return None for name."""
        name = self.checker.get_holiday_name(date(2025, 1, 7))
        self.assertIsNone(name)


class TestHolidayCheckerNoCountry(unittest.TestCase):
    """Test cases for HolidayChecker without country specification."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = HolidayChecker(None)

    def test_no_country_never_holiday(self):
        """Test that without country, no date is a holiday."""
        # New Year's Day - would be holiday in many countries
        self.assertFalse(self.checker.is_holiday(date(2025, 1, 1)))
        # Regular day
        self.assertFalse(self.checker.is_holiday(date(2025, 6, 15)))

    def test_get_holiday_name_no_country(self):
        """Test that get_holiday_name returns None without country."""
        name = self.checker.get_holiday_name(date(2025, 1, 1))
        self.assertIsNone(name)


class TestHolidayCheckerInvalidCountry(unittest.TestCase):
    """Test cases for HolidayChecker with invalid country codes."""

    def test_invalid_country_code_raises_error(self):
        """Test that invalid country code raises NotImplementedError."""
        with self.assertRaises(NotImplementedError) as context:
            HolidayChecker("INVALID")

        self.assertIn("INVALID", str(context.exception))
        self.assertIn("not supported", str(context.exception))


if __name__ == "__main__":
    unittest.main()
