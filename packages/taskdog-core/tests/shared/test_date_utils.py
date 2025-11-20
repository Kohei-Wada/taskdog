"""Tests for date utility functions."""

import unittest
from datetime import date, datetime

from parameterized import parameterized

from taskdog_core.shared.utils.date_utils import (
    calculate_next_workday,
    get_previous_monday,
    is_weekday,
    is_weekend,
)


class TestDateUtils(unittest.TestCase):
    """Test cases for date utility functions."""

    @parameterized.expand(
        [
            ("monday", datetime(2025, 1, 6), 0, datetime(2025, 1, 6)),
            ("friday", datetime(2025, 1, 10), 4, datetime(2025, 1, 10)),
            ("saturday_to_monday", datetime(2025, 1, 4), 0, datetime(2025, 1, 6)),
            ("sunday_to_monday", datetime(2025, 1, 5), 0, datetime(2025, 1, 6)),
        ]
    )
    def test_calculate_next_workday(
        self, _scenario, input_date, expected_weekday, expected_date
    ):
        """Test calculation for various days of the week."""
        result = calculate_next_workday(input_date)
        self.assertEqual(result.weekday(), expected_weekday)
        self.assertEqual(result.date(), expected_date.date())


class TestGetPreviousMonday(unittest.TestCase):
    """Test cases for get_previous_monday function."""

    @parameterized.expand(
        [
            ("monday", date(2025, 1, 6), date(2025, 1, 6)),
            ("tuesday", date(2025, 1, 7), date(2025, 1, 6)),
            ("wednesday", date(2025, 1, 8), date(2025, 1, 6)),
            ("sunday", date(2025, 1, 12), date(2025, 1, 6)),
        ]
    )
    def test_get_previous_monday_for_weekday(
        self, _scenario, input_date, expected_monday
    ):
        """Test that various days return the correct previous Monday."""
        result = get_previous_monday(input_date)
        self.assertEqual(result, expected_monday)
        self.assertEqual(result.weekday(), 0)

    def test_get_previous_monday_default_none(self):
        """Test that None uses today's date."""
        result = get_previous_monday(None)
        # Should return a Monday
        self.assertEqual(result.weekday(), 0)
        # Should be <= today
        self.assertLessEqual(result, date.today())

    def test_get_previous_monday_no_argument(self):
        """Test that no argument uses today's date."""
        result = get_previous_monday()
        # Should return a Monday
        self.assertEqual(result.weekday(), 0)
        # Should be <= today
        self.assertLessEqual(result, date.today())


class TestWeekdayHelpers(unittest.TestCase):
    """Test cases for is_weekday and is_weekend helper functions."""

    @parameterized.expand(
        [
            ("monday", date(2025, 1, 6), True, False),
            ("friday", date(2025, 1, 10), True, False),
            ("saturday", date(2025, 1, 4), False, True),
            ("sunday", date(2025, 1, 5), False, True),
        ]
    )
    def test_weekday_weekend_classification(
        self, _scenario, test_date, is_weekday_expected, is_weekend_expected
    ):
        """Test that dates are correctly classified as weekday or weekend."""
        self.assertEqual(is_weekday(test_date), is_weekday_expected)
        self.assertEqual(is_weekend(test_date), is_weekend_expected)

    def test_is_weekday_with_datetime(self):
        """Test that helper functions work with datetime objects."""
        monday_dt = datetime(2025, 1, 6, 10, 30)  # Monday 10:30
        saturday_dt = datetime(2025, 1, 4, 15, 45)  # Saturday 15:45

        self.assertTrue(is_weekday(monday_dt))
        self.assertFalse(is_weekend(monday_dt))
        self.assertFalse(is_weekday(saturday_dt))
        self.assertTrue(is_weekend(saturday_dt))


if __name__ == "__main__":
    unittest.main()
