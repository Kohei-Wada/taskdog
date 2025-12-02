"""Tests for date utility functions."""

from datetime import date, datetime

import pytest

from taskdog_core.shared.utils.date_utils import (
    calculate_next_workday,
    get_previous_monday,
    is_weekday,
    is_weekend,
)


class TestDateUtils:
    """Test cases for date utility functions."""

    @pytest.mark.parametrize(
        "input_date,expected_weekday,expected_date",
        [
            (datetime(2025, 1, 6), 0, datetime(2025, 1, 6)),
            (datetime(2025, 1, 10), 4, datetime(2025, 1, 10)),
            (datetime(2025, 1, 4), 0, datetime(2025, 1, 6)),
            (datetime(2025, 1, 5), 0, datetime(2025, 1, 6)),
        ],
        ids=["monday", "friday", "saturday_to_monday", "sunday_to_monday"],
    )
    def test_calculate_next_workday(self, input_date, expected_weekday, expected_date):
        """Test calculation for various days of the week."""
        result = calculate_next_workday(input_date)
        assert result.weekday() == expected_weekday
        assert result.date() == expected_date.date()


class TestGetPreviousMonday:
    """Test cases for get_previous_monday function."""

    @pytest.mark.parametrize(
        "input_date,expected_monday",
        [
            (date(2025, 1, 6), date(2025, 1, 6)),
            (date(2025, 1, 7), date(2025, 1, 6)),
            (date(2025, 1, 8), date(2025, 1, 6)),
            (date(2025, 1, 12), date(2025, 1, 6)),
        ],
        ids=["monday", "tuesday", "wednesday", "sunday"],
    )
    def test_get_previous_monday_for_weekday(self, input_date, expected_monday):
        """Test that various days return the correct previous Monday."""
        result = get_previous_monday(input_date)
        assert result == expected_monday
        assert result.weekday() == 0

    def test_get_previous_monday_default_none(self):
        """Test that None uses today's date."""
        result = get_previous_monday(None)
        # Should return a Monday
        assert result.weekday() == 0
        # Should be <= today
        assert result <= date.today()

    def test_get_previous_monday_no_argument(self):
        """Test that no argument uses today's date."""
        result = get_previous_monday()
        # Should return a Monday
        assert result.weekday() == 0
        # Should be <= today
        assert result <= date.today()


class TestWeekdayHelpers:
    """Test cases for is_weekday and is_weekend helper functions."""

    @pytest.mark.parametrize(
        "test_date,is_weekday_expected,is_weekend_expected",
        [
            (date(2025, 1, 6), True, False),
            (date(2025, 1, 10), True, False),
            (date(2025, 1, 4), False, True),
            (date(2025, 1, 5), False, True),
        ],
        ids=["monday", "friday", "saturday", "sunday"],
    )
    def test_weekday_weekend_classification(
        self, test_date, is_weekday_expected, is_weekend_expected
    ):
        """Test that dates are correctly classified as weekday or weekend."""
        assert is_weekday(test_date) == is_weekday_expected
        assert is_weekend(test_date) == is_weekend_expected

    def test_is_weekday_with_datetime(self):
        """Test that helper functions work with datetime objects."""
        monday_dt = datetime(2025, 1, 6, 10, 30)  # Monday 10:30
        saturday_dt = datetime(2025, 1, 4, 15, 45)  # Saturday 15:45

        assert is_weekday(monday_dt) is True
        assert is_weekend(monday_dt) is False
        assert is_weekday(saturday_dt) is False
        assert is_weekend(saturday_dt) is True
