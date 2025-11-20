"""Tests for HolidayChecker utility."""

import unittest
from datetime import date

from parameterized import parameterized

from taskdog_core.infrastructure.holiday_checker import HolidayChecker


class TestHolidayCheckerJapan(unittest.TestCase):
    """Test cases for HolidayChecker with Japanese holidays."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = HolidayChecker("JP")

    @parameterized.expand(
        [
            ("new_years_day", date(2025, 1, 1), True),
            ("showa_day", date(2025, 4, 29), True),
            ("constitution_day", date(2025, 5, 3), True),
            ("greenery_day", date(2025, 5, 4), True),
            ("childrens_day", date(2025, 5, 5), True),
            ("regular_weekday", date(2025, 1, 7), False),
            ("regular_weekend", date(2025, 1, 4), False),
        ]
    )
    def test_is_holiday_japan(self, _scenario, test_date, expected_is_holiday):
        """Test Japanese holiday detection."""
        self.assertEqual(self.checker.is_holiday(test_date), expected_is_holiday)

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
