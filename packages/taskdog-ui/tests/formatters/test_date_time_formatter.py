"""Tests for DateTimeFormatter."""

from datetime import datetime
from unittest.mock import patch

import pytest

from taskdog.formatters.date_time_formatter import DateTimeFormatter


class TestDateTimeFormatter:
    """Test cases for DateTimeFormatter."""

    def test_format_datetime_none(self):
        """Test formatting None datetime returns dash."""
        result = DateTimeFormatter.format_datetime(None)
        assert result == "-"

    def test_format_datetime_current_year(self):
        """Test formatting datetime in current year hides year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2025, 3, 10, 14, 30, 0)
            result = DateTimeFormatter.format_datetime(dt)
            assert result == "03-10 14:30"

    def test_format_datetime_different_year(self):
        """Test formatting datetime in different year shows year."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            dt = datetime(2024, 12, 25, 18, 45, 0)
            result = DateTimeFormatter.format_datetime(dt)
            assert result == "'24 12-25 18:45"

    @pytest.mark.parametrize(
        "dt,show_year,expected",
        [
            (datetime(2025, 3, 10, 14, 30, 0), True, "'25 03-10 14:30"),
            (datetime(2024, 12, 25, 18, 45, 0), False, "12-25 18:45"),
        ],
        ids=["show_year_true", "show_year_false"],
    )
    def test_format_datetime_with_show_year_parameter(self, dt, show_year, expected):
        """Test format_datetime with explicit show_year parameter."""
        result = DateTimeFormatter.format_datetime(dt, show_year=show_year)
        assert result == expected

    @pytest.mark.parametrize(
        "method_name,dt,expected",
        [
            ("format_deadline", datetime(2025, 7, 20, 23, 59, 0), "07-20 23:59"),
            ("format_planned_start", datetime(2025, 6, 1, 9, 0, 0), "06-01 09:00"),
            ("format_planned_end", datetime(2025, 6, 5, 17, 0, 0), "06-05 17:00"),
            ("format_actual_start", datetime(2025, 6, 2, 10, 30, 0), "06-02 10:30"),
            ("format_actual_end", datetime(2025, 6, 4, 16, 45, 0), "06-04 16:45"),
        ],
        ids=["deadline", "planned_start", "planned_end", "actual_start", "actual_end"],
    )
    def test_format_datetime_delegates(self, method_name, dt, expected):
        """Test that specialized format methods delegate to format_datetime."""
        with patch("taskdog.formatters.date_time_formatter.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15, 12, 0, 0)
            method = getattr(DateTimeFormatter, method_name)
            result = method(dt)
            assert result == expected

    def test_format_deadline_none(self):
        """Test format_deadline with None returns dash."""
        result = DateTimeFormatter.format_deadline(None)
        assert result == "-"
