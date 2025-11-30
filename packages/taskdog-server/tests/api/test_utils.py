"""Tests for API utility functions."""

import unittest
from datetime import date

from fastapi import HTTPException

from taskdog_server.api.utils import parse_iso_date


class TestParseIsoDate(unittest.TestCase):
    """Test cases for parse_iso_date."""

    def test_parse_valid_date(self):
        """Valid ISO date string should be parsed correctly."""
        result = parse_iso_date("2025-01-15")
        self.assertEqual(result, date(2025, 1, 15))

    def test_parse_valid_datetime(self):
        """Valid ISO datetime string should return date part."""
        result = parse_iso_date("2025-01-15T10:30:00")
        self.assertEqual(result, date(2025, 1, 15))

    def test_parse_none_returns_none(self):
        """None input should return None."""
        result = parse_iso_date(None)
        self.assertIsNone(result)

    def test_parse_empty_string_returns_none(self):
        """Empty string should return None."""
        result = parse_iso_date("")
        self.assertIsNone(result)

    def test_parse_invalid_format_raises_exception(self):
        """Invalid date format should raise HTTPException with 400."""
        with self.assertRaises(HTTPException) as cm:
            parse_iso_date("invalid-date")
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("Invalid date format", cm.exception.detail)

    def test_parse_invalid_date_raises_exception(self):
        """Invalid date (e.g., Feb 30) should raise HTTPException."""
        with self.assertRaises(HTTPException) as cm:
            parse_iso_date("2025-02-30")
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("Invalid date format", cm.exception.detail)


if __name__ == "__main__":
    unittest.main()
