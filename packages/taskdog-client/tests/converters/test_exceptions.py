"""Tests for ConversionError exception."""

import pytest
from taskdog_client.converters.exceptions import ConversionError


class TestConversionError:
    """Test cases for ConversionError exception."""

    def test_basic_error_message(self):
        """Test creating error with just a message."""
        error = ConversionError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.field is None
        assert error.value is None

    def test_error_with_field(self):
        """Test creating error with field name."""
        error = ConversionError("Invalid value", field="deadline")

        assert str(error) == "Invalid value"
        assert error.field == "deadline"
        assert error.value is None

    def test_error_with_field_and_value(self):
        """Test creating error with field name and value."""
        error = ConversionError(
            "Failed to parse datetime",
            field="created_at",
            value="invalid-date",
        )

        assert str(error) == "Failed to parse datetime"
        assert error.field == "created_at"
        assert error.value == "invalid-date"

    def test_error_with_none_value(self):
        """Test creating error with None as value."""
        error = ConversionError(
            "Required field is missing",
            field="updated_at",
            value=None,
        )

        assert error.field == "updated_at"
        assert error.value is None

    def test_error_with_complex_value(self):
        """Test creating error with complex value (dict)."""
        bad_value = {"invalid": "data", "nested": {"key": "value"}}
        error = ConversionError(
            "Failed to parse dictionary",
            field="daily_allocations",
            value=bad_value,
        )

        assert error.field == "daily_allocations"
        assert error.value == bad_value

    def test_error_is_exception(self):
        """Test that ConversionError is an Exception."""
        error = ConversionError("Test error")
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Test that ConversionError can be raised and caught."""
        with pytest.raises(ConversionError) as exc_info:
            raise ConversionError("Test raise", field="test_field", value=123)

        assert exc_info.value.field == "test_field"
        assert exc_info.value.value == 123
