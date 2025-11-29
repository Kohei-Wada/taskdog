"""Tests for ConversionError exception."""

import unittest

from taskdog.infrastructure.api.converters.exceptions import ConversionError


class TestConversionError(unittest.TestCase):
    """Test cases for ConversionError exception."""

    def test_basic_error_message(self):
        """Test creating error with just a message."""
        error = ConversionError("Something went wrong")

        self.assertEqual(str(error), "Something went wrong")
        self.assertIsNone(error.field)
        self.assertIsNone(error.value)

    def test_error_with_field(self):
        """Test creating error with field name."""
        error = ConversionError("Invalid value", field="deadline")

        self.assertEqual(str(error), "Invalid value")
        self.assertEqual(error.field, "deadline")
        self.assertIsNone(error.value)

    def test_error_with_field_and_value(self):
        """Test creating error with field name and value."""
        error = ConversionError(
            "Failed to parse datetime",
            field="created_at",
            value="invalid-date",
        )

        self.assertEqual(str(error), "Failed to parse datetime")
        self.assertEqual(error.field, "created_at")
        self.assertEqual(error.value, "invalid-date")

    def test_error_with_none_value(self):
        """Test creating error with None as value."""
        error = ConversionError(
            "Required field is missing",
            field="updated_at",
            value=None,
        )

        self.assertEqual(error.field, "updated_at")
        self.assertIsNone(error.value)

    def test_error_with_complex_value(self):
        """Test creating error with complex value (dict)."""
        bad_value = {"invalid": "data", "nested": {"key": "value"}}
        error = ConversionError(
            "Failed to parse dictionary",
            field="daily_allocations",
            value=bad_value,
        )

        self.assertEqual(error.field, "daily_allocations")
        self.assertEqual(error.value, bad_value)

    def test_error_is_exception(self):
        """Test that ConversionError is an Exception."""
        error = ConversionError("Test error")
        self.assertIsInstance(error, Exception)

    def test_error_can_be_raised(self):
        """Test that ConversionError can be raised and caught."""
        with self.assertRaises(ConversionError) as context:
            raise ConversionError("Test raise", field="test_field", value=123)

        self.assertEqual(context.exception.field, "test_field")
        self.assertEqual(context.exception.value, 123)


if __name__ == "__main__":
    unittest.main()
