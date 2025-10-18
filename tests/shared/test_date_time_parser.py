"""Tests for DateTimeParser utility."""

import unittest
from datetime import date, datetime

from shared.utils.date_utils import DateTimeParser


class DateTimeParserTest(unittest.TestCase):
    """Test cases for DateTimeParser."""

    def test_parse_date_valid(self):
        """Test date parsing with valid input."""
        result = DateTimeParser.parse_date("2025-01-06 09:00:00")
        self.assertEqual(result, date(2025, 1, 6))

    def test_parse_date_invalid(self):
        """Test date parsing with invalid input."""
        result = DateTimeParser.parse_date("invalid-date")
        self.assertIsNone(result)

    def test_parse_date_none(self):
        """Test date parsing with None input."""
        result = DateTimeParser.parse_date(None)
        self.assertIsNone(result)

    def test_parse_date_extracts_date_part(self):
        """Test that parse_date correctly extracts date part from datetime string."""
        result = DateTimeParser.parse_date("2025-12-25 23:59:59")
        self.assertEqual(result, date(2025, 12, 25))

    def test_parse_datetime_valid(self):
        """Test datetime parsing with valid input."""
        result = DateTimeParser.parse_datetime("2025-01-06 09:30:45")
        self.assertEqual(result, datetime(2025, 1, 6, 9, 30, 45))

    def test_parse_datetime_invalid(self):
        """Test datetime parsing with invalid input."""
        result = DateTimeParser.parse_datetime("invalid-datetime")
        self.assertIsNone(result)

    def test_parse_datetime_none(self):
        """Test datetime parsing with None input."""
        result = DateTimeParser.parse_datetime(None)
        self.assertIsNone(result)

    def test_parse_datetime_preserves_time(self):
        """Test that parse_datetime preserves time information."""
        result = DateTimeParser.parse_datetime("2025-12-25 23:59:59")
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
        self.assertEqual(result.second, 59)


if __name__ == "__main__":
    unittest.main()
