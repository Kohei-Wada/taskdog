"""Tests for API utility functions."""

from datetime import date

import pytest
from fastapi import HTTPException

from taskdog_server.api.utils import parse_iso_date


class TestParseIsoDate:
    """Test cases for parse_iso_date."""

    def test_parse_valid_date(self):
        """Valid ISO date string should be parsed correctly."""
        result = parse_iso_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_parse_valid_datetime(self):
        """Valid ISO datetime string should return date part."""
        result = parse_iso_date("2025-01-15T10:30:00")
        assert result == date(2025, 1, 15)

    def test_parse_none_returns_none(self):
        """None input should return None."""
        result = parse_iso_date(None)
        assert result is None

    def test_parse_empty_string_returns_none(self):
        """Empty string should return None."""
        result = parse_iso_date("")
        assert result is None

    def test_parse_invalid_format_raises_exception(self):
        """Invalid date format should raise HTTPException with 400."""
        with pytest.raises(HTTPException) as exc_info:
            parse_iso_date("invalid-date")
        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    def test_parse_invalid_date_raises_exception(self):
        """Invalid date (e.g., Feb 30) should raise HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            parse_iso_date("2025-02-30")
        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail
