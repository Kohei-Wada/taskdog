"""Tests for DateTimeParser utility."""

import unittest
from datetime import date, datetime

from parameterized import parameterized

from taskdog_core.shared.utils.date_utils import parse_date, parse_datetime


class DateTimeParserTest(unittest.TestCase):
    """Test cases for parse_date and parse_datetime functions."""

    @parameterized.expand(
        [
            ("valid_datetime_string", "2025-01-06 09:00:00", date(2025, 1, 6)),
            ("date_with_time", "2025-12-25 23:59:59", date(2025, 12, 25)),
            ("invalid_string", "invalid-date", None),
            ("none_input", None, None),
        ]
    )
    def test_parse_date(self, _scenario, input_str, expected_result):
        """Test parse_date with various inputs."""
        result = parse_date(input_str)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            ("valid_datetime", "2025-01-06 09:30:45", datetime(2025, 1, 6, 9, 30, 45)),
            (
                "preserves_time",
                "2025-12-25 23:59:59",
                datetime(2025, 12, 25, 23, 59, 59),
            ),
            ("invalid_string", "invalid-datetime", None),
            ("none_input", None, None),
        ]
    )
    def test_parse_datetime(self, _scenario, input_str, expected_result):
        """Test parse_datetime with various inputs."""
        result = parse_datetime(input_str)
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
