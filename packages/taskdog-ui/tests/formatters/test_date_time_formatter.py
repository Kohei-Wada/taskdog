"""Tests for DateTimeFormatter."""

import unittest
from datetime import datetime
from unittest.mock import patch

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

    def test_format_datetime_with_show_year_true(self):
        """Test format_datetime with show_year=True always shows year."""
        dt = datetime(2025, 3, 10, 14, 30, 0)
        result = DateTimeFormatter.format_datetime(dt, show_year=True)
        self.assertEqual(result, "'25 03-10 14:30")

    def test_format_datetime_with_show_year_false(self):
        """Test format_datetime with show_year=False never shows year."""
        dt = datetime(2024, 12, 25, 18, 45, 0)
        result = DateTimeFormatter.format_datetime(dt, show_year=False)
        self.assertEqual(result, "12-25 18:45")

    def test_format_deadline(self):
        """Test format_deadline delegates to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            deadline = datetime(2025, 7, 20, 23, 59, 0)
            result = DateTimeFormatter.format_deadline(deadline)
            self.assertEqual(result, "07-20 23:59")

    def test_format_deadline_none(self):
        """Test format_deadline with None returns dash."""
        result = DateTimeFormatter.format_deadline(None)
        self.assertEqual(result, "-")

    def test_format_planned_start(self):
        """Test format_planned_start delegates to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            planned_start = datetime(2025, 6, 1, 9, 0, 0)
            result = DateTimeFormatter.format_planned_start(planned_start)
            self.assertEqual(result, "06-01 09:00")

    def test_format_planned_end(self):
        """Test format_planned_end delegates to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            planned_end = datetime(2025, 6, 5, 17, 0, 0)
            result = DateTimeFormatter.format_planned_end(planned_end)
            self.assertEqual(result, "06-05 17:00")

    def test_format_actual_start(self):
        """Test format_actual_start delegates to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            actual_start = datetime(2025, 6, 2, 10, 30, 0)
            result = DateTimeFormatter.format_actual_start(actual_start)
            self.assertEqual(result, "06-02 10:30")

    def test_format_actual_end(self):
        """Test format_actual_end delegates to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            actual_end = datetime(2025, 6, 4, 16, 45, 0)
            result = DateTimeFormatter.format_actual_end(actual_end)
            self.assertEqual(result, "06-04 16:45")

    def test_should_show_year_same_year(self):
        """Test should_show_year returns False for current year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2025, 12, 31, 23, 59, 0)
            result = DateTimeFormatter.should_show_year(dt)
            self.assertFalse(result)

    def test_should_show_year_different_year(self):
        """Test should_show_year returns True for different year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2024, 1, 1, 0, 0, 0)
            result = DateTimeFormatter.should_show_year(dt)
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
