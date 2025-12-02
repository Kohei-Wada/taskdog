"""Tests for ISO datetime parser utilities."""

from datetime import date, datetime

import pytest

from taskdog_core.shared.utils.datetime_parser import (
    format_iso_date,
    format_iso_datetime,
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

    @pytest.mark.parametrize(
        "invalid_input",
        ["invalid-datetime"],
        ids=["invalid_format"],
    )
    def test_invalid_format_raises_valueerror(self, invalid_input):
        """Invalid format should raise ValueError."""
        with pytest.raises(ValueError):
            parse_iso_datetime(invalid_input)


class TestFormatIsoDatetime:
    """Test cases for format_iso_datetime."""

    def test_format_datetime(self):
        """Datetime should format to ISO string."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = format_iso_datetime(dt)
        assert result == "2025-01-15T10:30:00"

    def test_format_datetime_with_micros(self):
        """Datetime with microseconds should include them."""
        dt = datetime(2025, 1, 15, 10, 30, 0, 123456)
        result = format_iso_datetime(dt)
        assert result == "2025-01-15T10:30:00.123456"

    def test_none_returns_none(self):
        """None input should return None."""
        assert format_iso_datetime(None) is None


class TestFormatIsoDate:
    """Test cases for format_iso_date."""

    def test_format_date(self):
        """Date should format to ISO string."""
        d = date(2025, 1, 15)
        result = format_iso_date(d)
        assert result == "2025-01-15"

    def test_none_returns_none(self):
        """None input should return None."""
        assert format_iso_date(None) is None
