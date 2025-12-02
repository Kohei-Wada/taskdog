"""Tests for PositiveFloat and PositiveInt Click types."""

from unittest.mock import Mock

import click
import pytest

from taskdog.shared.click_types.positive_number import PositiveFloat, PositiveInt


class TestPositiveFloat:
    """Test cases for PositiveFloat Click type."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.param_type = PositiveFloat()
        self.param = Mock()
        self.ctx = Mock()

    @pytest.mark.parametrize(
        "input_str,expected_value,expected_error",
        [
            ("10.5", 10.5, None),
            ("0.1", 0.1, None),
            ("100.0", 100.0, None),
            ("10", 10.0, None),
            ("1", 1.0, None),
            ("0", None, "not a valid positive number"),
            ("0.0", None, "not a valid positive number"),
            ("-5.5", None, "not a valid positive number"),
            ("-1", None, "not a valid positive number"),
            ("abc", None, "not a valid number"),
            ("10.5.5", None, "not a valid number"),
        ],
        ids=[
            "positive_float",
            "small_positive",
            "large_positive",
            "integer_string",
            "integer_one",
            "zero",
            "zero_float",
            "negative",
            "negative_int",
            "invalid_string",
            "malformed",
        ],
    )
    def test_positive_float_validation(self, input_str, expected_value, expected_error):
        """Test PositiveFloat validation with various inputs."""
        if expected_error is None:
            result = self.param_type.convert(input_str, self.param, self.ctx)
            assert result == expected_value
        else:
            with pytest.raises(click.exceptions.BadParameter) as exc_info:
                self.param_type.convert(input_str, self.param, self.ctx)
            assert expected_error in str(exc_info.value)

    def test_type_name(self):
        """Test that the type has correct name."""
        assert self.param_type.name == "positive_float"


class TestPositiveInt:
    """Test cases for PositiveInt Click type."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.param_type = PositiveInt()
        self.param = Mock()
        self.ctx = Mock()

    @pytest.mark.parametrize(
        "input_str,expected_value,expected_error",
        [
            ("10", 10, None),
            ("1", 1, None),
            ("100", 100, None),
            ("0", None, "not a valid positive integer"),
            ("-5", None, "not a valid positive integer"),
            ("-1", None, "not a valid positive integer"),
            ("10.5", None, "not a valid integer"),
            ("abc", None, "not a valid integer"),
            ("10.5.5", None, "not a valid integer"),
        ],
        ids=[
            "positive_int",
            "small_positive",
            "large_positive",
            "zero",
            "negative",
            "negative_one",
            "float_string",
            "invalid_string",
            "malformed",
        ],
    )
    def test_positive_int_validation(self, input_str, expected_value, expected_error):
        """Test PositiveInt validation with various inputs."""
        if expected_error is None:
            result = self.param_type.convert(input_str, self.param, self.ctx)
            assert result == expected_value
        else:
            with pytest.raises(click.exceptions.BadParameter) as exc_info:
                self.param_type.convert(input_str, self.param, self.ctx)
            assert expected_error in str(exc_info.value)

    def test_type_name(self):
        """Test that the type has correct name."""
        assert self.param_type.name == "positive_int"
