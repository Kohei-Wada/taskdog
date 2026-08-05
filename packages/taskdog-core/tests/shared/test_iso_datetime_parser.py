"""Tests for ISO datetime parser utilities."""

from datetime import date, datetime

import pytest

from taskdog_core.shared.utils.datetime_parser import (
    format_date_dict,
    parse_iso_date,
    parse_iso_datetime,
)


class TestParseIsoDate:
    """Test cases for parse_iso_date."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("2025-01-15", date(2025, 1, 15)),
            ("2025-01-15T10:30:00", date(2025, 1, 15)),
            ("2025-01-15T10:30:00.123456", date(2025, 1, 15)),
        ],
        ids=["date_only", "datetime_string", "datetime_with_micros"],
    )
    def test_valid_date_strings(self, input_str, expected):
        """Valid ISO date strings should parse correctly."""
        result = parse_iso_date(input_str)
        assert result == expected

    def test_none_returns_none(self):
        """None input should return None."""
        assert parse_iso_date(None) is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert parse_iso_date("") is None

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "invalid-date",
            "2025/01/15",
            "2025-13-01",
            "2025-02-30",
        ],
        ids=["invalid_format", "wrong_separator", "invalid_month", "invalid_day"],
    )
    def test_invalid_format_raises_valueerror(self, invalid_input):
        """Invalid format should raise ValueError."""
        with pytest.raises(ValueError):
            parse_iso_date(invalid_input)


class TestParseIsoDatetime:
    """Test cases for parse_iso_datetime."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("2025-01-15T10:30:00", datetime(2025, 1, 15, 10, 30, 0)),
            ("2025-01-15T10:30:45.123456", datetime(2025, 1, 15, 10, 30, 45, 123456)),
            ("2025-12-31T00:00:00", datetime(2025, 12, 31, 0, 0, 0)),
        ],
        ids=["basic", "with_micros", "midnight"],
    )
    def test_valid_datetime_strings(self, input_str, expected):
        """Valid ISO datetime strings should parse correctly."""
        result = parse_iso_datetime(input_str)
        assert result == expected

    def test_none_returns_none(self):
        """None input should return None."""
        assert parse_iso_datetime(None) is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert parse_iso_datetime("") is None

    def test_date_only_defaults_to_midnight(self):
        """Date-only input should parse to the start of that day."""
        assert parse_iso_datetime("2025-01-15") == datetime(2025, 1, 15, 0, 0, 0)

    def test_date_only_with_end_of_day_returns_last_microsecond(self):
        """end_of_day should push a date-only input to the end of that day."""
        assert parse_iso_datetime("2025-01-15", end_of_day=True) == datetime(
            2025, 1, 15, 23, 59, 59, 999999
        )

    def test_end_of_day_keeps_explicit_time(self):
        """end_of_day should not touch an input that already carries a time."""
        assert parse_iso_datetime("2025-01-15T10:30:00", end_of_day=True) == datetime(
            2025, 1, 15, 10, 30, 0
        )

    def test_end_of_day_keeps_explicit_midnight(self):
        """An explicit midnight is a real time, not a date-only value."""
        assert parse_iso_datetime("2025-01-15T00:00:00", end_of_day=True) == datetime(
            2025, 1, 15, 0, 0, 0
        )

    def test_end_of_day_with_none_returns_none(self):
        """None input should return None regardless of end_of_day."""
        assert parse_iso_datetime(None, end_of_day=True) is None

    @pytest.mark.parametrize(
        "invalid_input",
        ["invalid-datetime"],
        ids=["invalid_format"],
    )
    def test_invalid_format_raises_valueerror(self, invalid_input):
        """Invalid format should raise ValueError."""
        with pytest.raises(ValueError):
            parse_iso_datetime(invalid_input)


class TestFormatDateDict:
    """Test cases for format_date_dict."""

    def test_empty_dict_returns_empty(self):
        """Empty dict should return empty dict."""
        assert format_date_dict({}) == {}

    def test_format_dict_with_values(self):
        """Dict with date keys should format to ISO string keys."""
        input_dict = {
            date(2025, 1, 15): 2.5,
            date(2025, 1, 16): 3.0,
        }
        expected = {
            "2025-01-15": 2.5,
            "2025-01-16": 3.0,
        }
        assert format_date_dict(input_dict) == expected
