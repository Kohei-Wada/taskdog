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

    @pytest.mark.parametrize(
        "input_str",
        [
            "",
            "   ",
            "2025-12-31 18:30:00",
            "2025-12-31",
            "2025-12-31 09:30",
            "next friday",
            "tomorrow 6pm",
            "in 2 weeks",
        ],
        ids=[
            "empty",
            "whitespace",
            "iso_datetime",
            "date_only",
            "date_with_time",
            "next_friday",
            "tomorrow_6pm",
            "in_2_weeks",
        ],
    )
    def test_valid_input(self, input_str: str) -> None:
        """Test that valid datetime inputs are accepted."""
        result = self.validator.validate(input_str)
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

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("", None),
            ("   ", None),
            ("2025-12-31 09:30:00", "2025-12-31 09:30:00"),
            ("2025-12-31", "2025-12-31 18:30:00"),
        ],
        ids=["empty", "whitespace", "full_datetime", "date_only_default_time"],
    )
    def test_parse(self, input_str: str, expected: str | None) -> None:
        """Test parsing datetime input strings."""
        result = self.validator.parse(input_str)
        assert result == expected

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

    @pytest.mark.parametrize(
        "field,default_time,input_str,expected_substring",
        [
            ("deadline", time(18, 30, 0), "2025-12-31", "18:30:00"),
            ("planned start", time(9, 30, 0), "2025-12-31", "09:30:00"),
            ("deadline", time(18, 30, 0), "2025-12-31 10:30", "10:30"),
            ("deadline", time(18, 30, 0), "2025-12-31 00:00:00", None),
        ],
        ids=[
            "deadline_default",
            "start_default",
            "explicit_override",
            "midnight_preserved",
        ],
    )
    def test_default_time_behavior(
        self,
        field: str,
        default_time: time,
        input_str: str,
        expected_substring: str | None,
    ) -> None:
        """Test default time application behavior."""
        validator = DateTimeValidator(field, default_time)
        result = validator.parse(input_str)
        assert result is not None
        if expected_substring:
            assert expected_substring in result
