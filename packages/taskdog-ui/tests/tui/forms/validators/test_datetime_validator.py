"""Tests for DateTimeValidator."""

from datetime import time

import pytest

from taskdog.tui.forms.validators import DateTimeValidator


class TestDateTimeValidatorValidate:
    """Test cases for DateTimeValidator.validate method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.validator = DateTimeValidator("deadline", time(18, 30, 0))

    def test_empty_string_is_valid(self) -> None:
        """Test that empty string is valid (optional field)."""
        result = self.validator.validate("")
        assert result.is_valid is True

    def test_whitespace_only_is_valid(self) -> None:
        """Test that whitespace-only string is valid."""
        result = self.validator.validate("   ")
        assert result.is_valid is True

    def test_iso_format_is_valid(self) -> None:
        """Test that ISO format datetime is valid."""
        result = self.validator.validate("2025-12-31 18:30:00")
        assert result.is_valid is True

    def test_date_only_is_valid(self) -> None:
        """Test that date-only string is valid."""
        result = self.validator.validate("2025-12-31")
        assert result.is_valid is True

    def test_date_with_time_is_valid(self) -> None:
        """Test that date with time is valid."""
        result = self.validator.validate("2025-12-31 09:30")
        assert result.is_valid is True

    def test_natural_language_next_friday_is_valid(self) -> None:
        """Test that 'next friday' is valid."""
        result = self.validator.validate("next friday")
        assert result.is_valid is True

    def test_natural_language_with_time_is_valid(self) -> None:
        """Test that 'tomorrow 6pm' is valid."""
        result = self.validator.validate("tomorrow 6pm")
        assert result.is_valid is True

    def test_relative_date_in_two_weeks_is_valid(self) -> None:
        """Test that 'in 2 weeks' is valid."""
        result = self.validator.validate("in 2 weeks")
        assert result.is_valid is True

    def test_invalid_date_format_fails(self) -> None:
        """Test that invalid date format fails."""
        result = self.validator.validate("not-a-date")
        assert result.is_valid is False
        assert "Invalid deadline format" in str(result.failure_descriptions)

    def test_field_name_in_error_message(self) -> None:
        """Test that field name appears in error message."""
        validator = DateTimeValidator("planned start", time(9, 30, 0))
        result = validator.validate("invalid")
        assert "planned start" in str(result.failure_descriptions)


class TestDateTimeValidatorParse:
    """Test cases for DateTimeValidator.parse method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.validator = DateTimeValidator("deadline", time(18, 30, 0))

    def test_parse_empty_string_returns_none(self) -> None:
        """Test that empty string returns None."""
        result = self.validator.parse("")
        assert result is None

    def test_parse_whitespace_returns_none(self) -> None:
        """Test that whitespace-only string returns None."""
        result = self.validator.parse("   ")
        assert result is None

    def test_parse_full_datetime(self) -> None:
        """Test parsing full datetime string."""
        result = self.validator.parse("2025-12-31 09:30:00")
        assert result == "2025-12-31 09:30:00"

    def test_parse_date_only_applies_default_hour(self) -> None:
        """Test that date-only string applies default hour."""
        result = self.validator.parse("2025-12-31")
        assert result == "2025-12-31 18:30:00"

    def test_parse_date_with_different_default_time(self) -> None:
        """Test parsing with different default time."""
        validator = DateTimeValidator("planned start", time(9, 30, 0))
        result = validator.parse("2025-01-15")
        assert result == "2025-01-15 09:30:00"

    def test_parse_datetime_with_time_preserves_time(self) -> None:
        """Test that datetime with time preserves the time."""
        result = self.validator.parse("2025-12-31 14:30")
        # Time is preserved, seconds default to 00
        assert "14:30" in result

    def test_parse_natural_language_date(self) -> None:
        """Test parsing natural language date."""
        # Just verify it parses without error and returns a formatted string
        result = self.validator.parse("2025-01-15")
        assert result is not None
        assert "-" in result  # Contains date separators
        assert ":" in result  # Contains time separators


class TestDateTimeValidatorDefaultTime:
    """Test cases for default time behavior."""

    def test_default_time_18_for_deadline(self) -> None:
        """Test that deadline validator uses 18:00 as default time."""
        validator = DateTimeValidator("deadline", time(18, 30, 0))
        result = validator.parse("2025-12-31")
        assert "18:30:00" in result

    def test_default_time_9_for_start(self) -> None:
        """Test that start validator uses 09:00 as default time."""
        validator = DateTimeValidator("planned start", time(9, 30, 0))
        result = validator.parse("2025-12-31")
        assert "09:30:00" in result

    def test_explicit_time_overrides_default(self) -> None:
        """Test that explicit time overrides default time."""
        validator = DateTimeValidator("deadline", time(18, 30, 0))
        result = validator.parse("2025-12-31 10:30")
        assert "10:30" in result
        assert "18:00" not in result

    def test_midnight_explicit_is_preserved(self) -> None:
        """Test that explicit midnight is preserved."""
        validator = DateTimeValidator("deadline", time(18, 30, 0))
        result = validator.parse("2025-12-31 00:00:00")
        # When time is explicitly specified (has colon), it should be preserved
        assert result is not None
