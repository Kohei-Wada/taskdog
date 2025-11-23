"""Tests for DateTimeFormatter."""

import unittest
from datetime import datetime
from unittest.mock import patch

from parameterized import parameterized

from taskdog.formatters.date_time_formatter import DateTimeFormatter


class TestDateTimeFormatter(unittest.TestCase):
    """Test cases for DateTimeFormatter."""

    def test_format_datetime_none(self):
        """Test formatting None datetime returns dash."""
        result = DateTimeFormatter.format_datetime(None)
        self.assertEqual(result, "-")

    def test_format_datetime_current_year(self):
        """Test formatting datetime in current year hides year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2025, 3, 10, 14, 30, 0)
            result = DateTimeFormatter.format_datetime(dt)
            self.assertEqual(result, "03-10 14:30")

    def test_format_datetime_different_year(self):
        """Test formatting datetime in different year shows year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2024, 12, 25, 18, 45, 0)
            result = DateTimeFormatter.format_datetime(dt)
            self.assertEqual(result, "'24 12-25 18:45")

    @parameterized.expand(
        [
            (
                "show_year_true",
                datetime(2025, 3, 10, 14, 30, 0),
                True,
                "'25 03-10 14:30",
            ),
            (
                "show_year_false",
                datetime(2024, 12, 25, 18, 45, 0),
                False,
                "12-25 18:45",
            ),
        ]
    )
    def test_format_datetime_with_show_year_parameter(
        self, scenario, dt, show_year, expected
    ):
        """Test format_datetime with explicit show_year parameter."""
        result = DateTimeFormatter.format_datetime(dt, show_year=show_year)
        self.assertEqual(result, expected)

    @parameterized.expand(
        [
            (
                "deadline",
                "format_deadline",
                datetime(2025, 7, 20, 23, 59, 0),
                "07-20 23:59",
            ),
            (
                "planned_start",
                "format_planned_start",
                datetime(2025, 6, 1, 9, 0, 0),
                "06-01 09:00",
            ),
            (
                "planned_end",
                "format_planned_end",
                datetime(2025, 6, 5, 17, 0, 0),
                "06-05 17:00",
            ),
            (
                "actual_start",
                "format_actual_start",
                datetime(2025, 6, 2, 10, 30, 0),
                "06-02 10:30",
            ),
            (
                "actual_end",
                "format_actual_end",
                datetime(2025, 6, 4, 16, 45, 0),
                "06-04 16:45",
            ),
        ]
    )
    def test_format_datetime_delegates(self, field, method_name, dt, expected):
        """Test that specialized format methods delegate to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            method = getattr(DateTimeFormatter, method_name)
            result = method(dt)
            self.assertEqual(result, expected)

    def test_format_deadline_none(self):
        """Test format_deadline with None returns dash."""
        result = DateTimeFormatter.format_deadline(None)
        self.assertEqual(result, "-")

    @parameterized.expand(
        [
            ("same_year", datetime(2025, 12, 31, 23, 59, 0), False),
            ("different_year", datetime(2024, 1, 1, 0, 0, 0), True),
        ]
    )
    def test_should_show_year(self, scenario, dt, expected):
        """Test should_show_year returns correct result based on year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            result = DateTimeFormatter.should_show_year(dt)
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
