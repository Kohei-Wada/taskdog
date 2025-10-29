"""Tests for PositiveFloat and PositiveInt Click types."""

import unittest
from unittest.mock import Mock

import click

from shared.click_types.positive_number import PositiveFloat, PositiveInt


class TestPositiveFloat(unittest.TestCase):
    """Test cases for PositiveFloat Click type."""

    def setUp(self):
        """Set up test fixtures."""
        self.param_type = PositiveFloat()
        self.param = Mock()
        self.ctx = Mock()

    def test_convert_positive_float_success(self):
        """Test that positive float values are accepted."""
        self.assertEqual(self.param_type.convert("10.5", self.param, self.ctx), 10.5)
        self.assertEqual(self.param_type.convert("0.1", self.param, self.ctx), 0.1)
        self.assertEqual(self.param_type.convert("100.0", self.param, self.ctx), 100.0)

    def test_convert_positive_integer_as_string_success(self):
        """Test that positive integer strings are converted to float."""
        self.assertEqual(self.param_type.convert("10", self.param, self.ctx), 10.0)
        self.assertEqual(self.param_type.convert("1", self.param, self.ctx), 1.0)

    def test_convert_zero_raises_error(self):
        """Test that zero value is rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("0", self.param, self.ctx)
        self.assertIn("not a valid positive number", str(context.exception))
        self.assertIn("must be greater than 0", str(context.exception))

    def test_convert_zero_float_raises_error(self):
        """Test that zero float value is rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("0.0", self.param, self.ctx)
        self.assertIn("not a valid positive number", str(context.exception))

    def test_convert_negative_raises_error(self):
        """Test that negative values are rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("-5.5", self.param, self.ctx)
        self.assertIn("not a valid positive number", str(context.exception))

        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("-1", self.param, self.ctx)
        self.assertIn("not a valid positive number", str(context.exception))

    def test_convert_invalid_string_raises_error(self):
        """Test that non-numeric strings are rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("abc", self.param, self.ctx)
        self.assertIn("not a valid number", str(context.exception))

        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("10.5.5", self.param, self.ctx)
        self.assertIn("not a valid number", str(context.exception))

    def test_type_name(self):
        """Test that the type has correct name."""
        self.assertEqual(self.param_type.name, "positive_float")


class TestPositiveInt(unittest.TestCase):
    """Test cases for PositiveInt Click type."""

    def setUp(self):
        """Set up test fixtures."""
        self.param_type = PositiveInt()
        self.param = Mock()
        self.ctx = Mock()

    def test_convert_positive_integer_success(self):
        """Test that positive integer values are accepted."""
        self.assertEqual(self.param_type.convert("10", self.param, self.ctx), 10)
        self.assertEqual(self.param_type.convert("1", self.param, self.ctx), 1)
        self.assertEqual(self.param_type.convert("100", self.param, self.ctx), 100)

    def test_convert_zero_raises_error(self):
        """Test that zero value is rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("0", self.param, self.ctx)
        self.assertIn("not a valid positive integer", str(context.exception))
        self.assertIn("must be greater than 0", str(context.exception))

    def test_convert_negative_raises_error(self):
        """Test that negative values are rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("-5", self.param, self.ctx)
        self.assertIn("not a valid positive integer", str(context.exception))

        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("-1", self.param, self.ctx)
        self.assertIn("not a valid positive integer", str(context.exception))

    def test_convert_float_string_raises_error(self):
        """Test that float strings are rejected (not valid integers)."""
        # int() cannot convert strings with decimal points directly
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("10.5", self.param, self.ctx)
        self.assertIn("not a valid integer", str(context.exception))

    def test_convert_invalid_string_raises_error(self):
        """Test that non-numeric strings are rejected."""
        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("abc", self.param, self.ctx)
        self.assertIn("not a valid integer", str(context.exception))

        with self.assertRaises(click.exceptions.BadParameter) as context:
            self.param_type.convert("10.5.5", self.param, self.ctx)
        self.assertIn("not a valid integer", str(context.exception))

    def test_type_name(self):
        """Test that the type has correct name."""
        self.assertEqual(self.param_type.name, "positive_int")


if __name__ == "__main__":
    unittest.main()
