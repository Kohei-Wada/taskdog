"""Tests for date utility functions."""

from datetime import date, datetime

import pytest

from taskdog_core.shared.utils.date_utils import (
    is_weekday,
    is_weekend,
)


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
