"""Tests for HolidayChecker utility."""

from datetime import date

import pytest

from taskdog_core.infrastructure.holiday_checker import HolidayChecker


class TestHolidayCheckerJapan:
    """Test cases for HolidayChecker with Japanese holidays."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.checker = HolidayChecker("JP")

    @pytest.mark.parametrize(
        "test_date,expected_is_holiday",
        [
            (date(2025, 1, 1), True),  # new_years_day
            (date(2025, 4, 29), True),  # showa_day
            (date(2025, 5, 3), True),  # constitution_day
            (date(2025, 5, 4), True),  # greenery_day
            (date(2025, 5, 5), True),  # childrens_day
            (date(2025, 1, 7), False),  # regular_weekday
            (date(2025, 1, 4), False),  # regular_weekend
        ],
        ids=[
            "new_years_day",
            "showa_day",
            "constitution_day",
            "greenery_day",
            "childrens_day",
            "regular_weekday",
            "regular_weekend",
        ],
    )
    def test_is_holiday_japan(self, test_date, expected_is_holiday):
        """Test Japanese holiday detection."""
        assert self.checker.is_holiday(test_date) == expected_is_holiday

    def test_get_holidays_in_range_single_month(self):
        """Test get_holidays_in_range for a single month."""
        # January 2025 in Japan has: Jan 1 (New Year), Jan 13 (Coming of Age Day)
        holidays = self.checker.get_holidays_in_range(
            date(2025, 1, 1), date(2025, 1, 31)
        )

        assert date(2025, 1, 1) in holidays  # New Year's Day
        assert date(2025, 1, 13) in holidays  # Coming of Age Day
        assert date(2025, 1, 7) not in holidays  # Regular day

    def test_get_holidays_in_range_across_years(self):
        """Test get_holidays_in_range spanning multiple years."""
        holidays = self.checker.get_holidays_in_range(
            date(2024, 2, 1), date(2025, 1, 31)
        )

        # Should include holidays from both years
        assert date(2024, 2, 23) in holidays  # Emperor's Birthday (2024)
        assert date(2025, 1, 1) in holidays  # New Year's Day (2025)

    def test_get_holidays_in_range_no_holidays(self):
        """Test get_holidays_in_range when no holidays in range."""
        # June typically has no holidays in Japan
        holidays = self.checker.get_holidays_in_range(
            date(2025, 6, 2), date(2025, 6, 7)
        )

        assert len(holidays) == 0

    def test_get_holidays_in_range_single_day(self):
        """Test get_holidays_in_range with single day range."""
        holidays = self.checker.get_holidays_in_range(
            date(2025, 1, 1), date(2025, 1, 1)
        )

        assert holidays == {date(2025, 1, 1)}

    def test_get_holidays_in_range_invalid_range(self):
        """Test get_holidays_in_range returns empty set when start > end."""
        holidays = self.checker.get_holidays_in_range(
            date(2025, 12, 31), date(2025, 1, 1)
        )

        assert holidays == set()


class TestHolidayCheckerNoCountry:
    """Test cases for HolidayChecker without country specification."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.checker = HolidayChecker(None)

    def test_no_country_never_holiday(self):
        """Test that without country, no date is a holiday."""
        # New Year's Day - would be holiday in many countries
        assert self.checker.is_holiday(date(2025, 1, 1)) is False
        # Regular day
        assert self.checker.is_holiday(date(2025, 6, 15)) is False

    def test_get_holidays_in_range_no_country(self):
        """Test that get_holidays_in_range returns empty set without country."""
        holidays = self.checker.get_holidays_in_range(
            date(2025, 1, 1), date(2025, 12, 31)
        )
        assert holidays == set()


class TestHolidayCheckerInvalidCountry:
    """Test cases for HolidayChecker with invalid country codes."""

    def test_invalid_country_code_raises_error(self):
        """Test that invalid country code raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            HolidayChecker("INVALID")

        assert "INVALID" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)
