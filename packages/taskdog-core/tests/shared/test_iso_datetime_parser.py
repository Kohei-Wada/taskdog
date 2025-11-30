"""Tests for ISO datetime parser utilities."""

import unittest
from datetime import date, datetime

from parameterized import parameterized

from taskdog_core.shared.utils.datetime_parser import (
    format_iso_date,
    format_iso_datetime,
    parse_iso_date,
    parse_iso_datetime,
)


class TestParseIsoDate(unittest.TestCase):
    """Test cases for parse_iso_date."""

    @parameterized.expand(
        [
            ("date_only", "2025-01-15", date(2025, 1, 15)),
            ("datetime_string", "2025-01-15T10:30:00", date(2025, 1, 15)),
            ("datetime_with_micros", "2025-01-15T10:30:00.123456", date(2025, 1, 15)),
        ]
    )
    def test_valid_date_strings(self, _name, input_str, expected):
        """Valid ISO date strings should parse correctly."""
        result = parse_iso_date(input_str)
        self.assertEqual(result, expected)

    def test_none_returns_none(self):
        """None input should return None."""
        self.assertIsNone(parse_iso_date(None))

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        self.assertIsNone(parse_iso_date(""))

    @parameterized.expand(
        [
            ("invalid_format", "invalid-date"),
            ("wrong_separator", "2025/01/15"),
            ("invalid_month", "2025-13-01"),
            ("invalid_day", "2025-02-30"),
        ]
    )
    def test_invalid_format_raises_valueerror(self, _name, invalid_input):
        """Invalid format should raise ValueError."""
        with self.assertRaises(ValueError):
            parse_iso_date(invalid_input)


class TestParseIsoDatetime(unittest.TestCase):
    """Test cases for parse_iso_datetime."""

    @parameterized.expand(
        [
            ("basic", "2025-01-15T10:30:00", datetime(2025, 1, 15, 10, 30, 0)),
            (
                "with_micros",
                "2025-01-15T10:30:45.123456",
                datetime(2025, 1, 15, 10, 30, 45, 123456),
            ),
            ("midnight", "2025-12-31T00:00:00", datetime(2025, 12, 31, 0, 0, 0)),
        ]
    )
    def test_valid_datetime_strings(self, _name, input_str, expected):
        """Valid ISO datetime strings should parse correctly."""
        result = parse_iso_datetime(input_str)
        self.assertEqual(result, expected)

    def test_none_returns_none(self):
        """None input should return None."""
        self.assertIsNone(parse_iso_datetime(None))

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        self.assertIsNone(parse_iso_datetime(""))

    @parameterized.expand(
        [
            ("invalid_format", "invalid-datetime"),
        ]
    )
    def test_invalid_format_raises_valueerror(self, _name, invalid_input):
        """Invalid format should raise ValueError."""
        with self.assertRaises(ValueError):
            parse_iso_datetime(invalid_input)


class TestFormatIsoDatetime(unittest.TestCase):
    """Test cases for format_iso_datetime."""

    def test_format_datetime(self):
        """Datetime should format to ISO string."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = format_iso_datetime(dt)
        self.assertEqual(result, "2025-01-15T10:30:00")

    def test_format_datetime_with_micros(self):
        """Datetime with microseconds should include them."""
        dt = datetime(2025, 1, 15, 10, 30, 0, 123456)
        result = format_iso_datetime(dt)
        self.assertEqual(result, "2025-01-15T10:30:00.123456")

    def test_none_returns_none(self):
        """None input should return None."""
        self.assertIsNone(format_iso_datetime(None))


class TestFormatIsoDate(unittest.TestCase):
    """Test cases for format_iso_date."""

    def test_format_date(self):
        """Date should format to ISO string."""
        d = date(2025, 1, 15)
        result = format_iso_date(d)
        self.assertEqual(result, "2025-01-15")

    def test_none_returns_none(self):
        """None input should return None."""
        self.assertIsNone(format_iso_date(None))


if __name__ == "__main__":
    unittest.main()
