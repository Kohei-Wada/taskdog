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

    def test_get_holiday_name(self):
        """Test that holiday names are retrieved correctly."""
        name = self.checker.get_holiday_name(date(2025, 1, 1))
        assert name is not None
        # Holiday name should contain something (varies by language)
        assert len(name) > 0

    def test_get_holiday_name_non_holiday(self):
        """Test that non-holidays return None for name."""
        name = self.checker.get_holiday_name(date(2025, 1, 7))
        assert name is None


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

    def test_get_holiday_name_no_country(self):
        """Test that get_holiday_name returns None without country."""
        name = self.checker.get_holiday_name(date(2025, 1, 1))
        assert name is None


class TestHolidayCheckerInvalidCountry:
    """Test cases for HolidayChecker with invalid country codes."""

    def test_invalid_country_code_raises_error(self):
        """Test that invalid country code raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            HolidayChecker("INVALID")

        assert "INVALID" in str(exc_info.value)
        assert "not supported" in str(exc_info.value)
