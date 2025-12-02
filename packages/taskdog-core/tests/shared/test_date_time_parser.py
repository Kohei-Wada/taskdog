"""Tests for DateTimeParser utility."""

from datetime import date, datetime

import pytest

from taskdog_core.shared.utils.date_utils import parse_date, parse_datetime


class TestDateTimeParser:
    """Test cases for parse_date and parse_datetime functions."""

    @pytest.mark.parametrize(
        "input_str,expected_result",
        [
            ("2025-01-06 09:00:00", date(2025, 1, 6)),
            ("2025-12-25 23:59:59", date(2025, 12, 25)),
            ("invalid-date", None),
            (None, None),
        ],
        ids=["valid_datetime_string", "date_with_time", "invalid_string", "none_input"],
    )
    def test_parse_date(self, input_str, expected_result):
        """Test parse_date with various inputs."""
        result = parse_date(input_str)
        assert result == expected_result

    @pytest.mark.parametrize(
        "input_str,expected_result",
        [
            ("2025-01-06 09:30:45", datetime(2025, 1, 6, 9, 30, 45)),
            ("2025-12-25 23:59:59", datetime(2025, 12, 25, 23, 59, 59)),
            ("invalid-datetime", None),
            (None, None),
        ],
        ids=["valid_datetime", "preserves_time", "invalid_string", "none_input"],
    )
    def test_parse_datetime(self, input_str, expected_result):
        """Test parse_datetime with various inputs."""
        result = parse_datetime(input_str)
        assert result == expected_result
