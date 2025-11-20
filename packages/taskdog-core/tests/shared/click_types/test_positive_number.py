"""Tests for PositiveFloat and PositiveInt Click types."""

import unittest
from unittest.mock import Mock

import click
from parameterized import parameterized

from taskdog_core.shared.click_types.positive_number import PositiveFloat, PositiveInt


class TestPositiveFloat(unittest.TestCase):
    """Test cases for PositiveFloat Click type."""

    def setUp(self):
        """Set up test fixtures."""
        self.param_type = PositiveFloat()
        self.param = Mock()
        self.ctx = Mock()

    @parameterized.expand(
        [
            ("positive_float", "10.5", 10.5, None),
            ("small_positive", "0.1", 0.1, None),
            ("large_positive", "100.0", 100.0, None),
            ("integer_string", "10", 10.0, None),
            ("integer_one", "1", 1.0, None),
            ("zero", "0", None, "not a valid positive number"),
            ("zero_float", "0.0", None, "not a valid positive number"),
            ("negative", "-5.5", None, "not a valid positive number"),
            ("negative_int", "-1", None, "not a valid positive number"),
            ("invalid_string", "abc", None, "not a valid number"),
            ("malformed", "10.5.5", None, "not a valid number"),
        ]
    )
    def test_positive_float_validation(
        self, _scenario, input_str, expected_value, expected_error
    ):
        """Test PositiveFloat validation with various inputs."""
        if expected_error is None:
            result = self.param_type.convert(input_str, self.param, self.ctx)
            self.assertEqual(result, expected_value)
        else:
            with self.assertRaises(click.exceptions.BadParameter) as context:
                self.param_type.convert(input_str, self.param, self.ctx)
            self.assertIn(expected_error, str(context.exception))

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

    @parameterized.expand(
        [
            ("positive_int", "10", 10, None),
            ("small_positive", "1", 1, None),
            ("large_positive", "100", 100, None),
            ("zero", "0", None, "not a valid positive integer"),
            ("negative", "-5", None, "not a valid positive integer"),
            ("negative_one", "-1", None, "not a valid positive integer"),
            ("float_string", "10.5", None, "not a valid integer"),
            ("invalid_string", "abc", None, "not a valid integer"),
            ("malformed", "10.5.5", None, "not a valid integer"),
        ]
    )
    def test_positive_int_validation(
        self, _scenario, input_str, expected_value, expected_error
    ):
        """Test PositiveInt validation with various inputs."""
        if expected_error is None:
            result = self.param_type.convert(input_str, self.param, self.ctx)
            self.assertEqual(result, expected_value)
        else:
            with self.assertRaises(click.exceptions.BadParameter) as context:
                self.param_type.convert(input_str, self.param, self.ctx)
            self.assertIn(expected_error, str(context.exception))

    def test_type_name(self):
        """Test that the type has correct name."""
        self.assertEqual(self.param_type.name, "positive_int")


if __name__ == "__main__":
    unittest.main()
