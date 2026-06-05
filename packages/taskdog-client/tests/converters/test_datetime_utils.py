"""Tests for datetime utility functions."""

from datetime import date

import pytest
from taskdog_client.converters.datetime_utils import (
    _parse_date_dict,
)
from taskdog_client.converters.exceptions import ConversionError


class TestParseDateDict:
    """Test cases for _parse_date_dict."""

    def test_valid_date_dict(self):
        """Test parsing valid date dictionary."""
        data = {
            "daily_allocations": {
                "2025-01-15": 2.5,
                "2025-01-16": 3.0,
                "2025-01-17": 1.5,
            }
        }

        result = _parse_date_dict(data, "daily_allocations")

        assert len(result) == 3
        assert result[date(2025, 1, 15)] == 2.5
        assert result[date(2025, 1, 16)] == 3.0
        assert result[date(2025, 1, 17)] == 1.5

    def test_empty_dict(self):
        """Test parsing empty dictionary."""
        data = {"daily_allocations": {}}
        result = _parse_date_dict(data, "daily_allocations")

        assert result == {}

    def test_missing_field(self):
        """Test parsing missing field returns empty dict."""
        data = {}
        result = _parse_date_dict(data, "daily_allocations")

        assert result == {}

    def test_invalid_date_key_raises_error(self):
        """Test that invalid date key raises ConversionError."""
        data = {
            "daily_allocations": {
                "2025-01-15": 2.5,
                "invalid-date": 3.0,
            }
        }

        with pytest.raises(ConversionError) as exc_info:
            _parse_date_dict(data, "daily_allocations")

        assert exc_info.value.field == "daily_allocations"

    def test_single_entry(self):
        """Test parsing dictionary with single entry."""
        data = {"daily_allocations": {"2025-01-20": 4.0}}

        result = _parse_date_dict(data, "daily_allocations")

        assert len(result) == 1
        assert result[date(2025, 1, 20)] == 4.0
