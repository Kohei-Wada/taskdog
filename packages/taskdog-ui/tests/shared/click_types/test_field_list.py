"""Tests for FieldList Click type."""

import unittest
from unittest.mock import Mock

import click
from parameterized import parameterized

from taskdog.shared.click_types.field_list import FieldList


class TestFieldList(unittest.TestCase):
    """Test cases for FieldList Click type."""

    def setUp(self):
        """Set up test fixtures."""
        self.param = Mock()
        self.ctx = Mock()

    @parameterized.expand(
        [
            ("single_field", "id", ["id"]),
            ("multiple_fields", "id,name,priority", ["id", "name", "priority"]),
            ("with_whitespace", "id, name , priority", ["id", "name", "priority"]),
            ("none_input", None, None),
            ("empty_string", "", None),
            ("whitespace_only", "   ", None),
        ]
    )
    def test_convert(self, _scenario, input_str, expected_result):
        """Test FieldList conversion with various inputs."""
        param_type = FieldList()
        result = param_type.convert(input_str, self.param, self.ctx)
        self.assertEqual(result, expected_result)

    def test_validation_with_valid_fields(self):
        """Test that valid fields pass validation."""
        valid_fields = {"id", "name", "priority", "status"}
        param_type = FieldList(valid_fields=valid_fields)
        result = param_type.convert("id,name,priority", self.param, self.ctx)

        self.assertEqual(result, ["id", "name", "priority"])

    @parameterized.expand(
        [
            (
                "single_invalid",
                {"id", "name", "priority"},
                "id,invalid,name",
                "Invalid field(s): invalid",
            ),
            (
                "multiple_invalid",
                {"id", "name"},
                "id,invalid1,invalid2,name",
                "Invalid field(s):",
            ),
            ("all_invalid", {"id", "name"}, "foo,bar", "Invalid field(s): foo, bar"),
        ]
    )
    def test_validation_errors(
        self, _scenario, valid_fields, input_str, expected_error
    ):
        """Test FieldList validation errors."""
        param_type = FieldList(valid_fields=valid_fields)
        with self.assertRaises(click.exceptions.BadParameter) as context:
            param_type.convert(input_str, self.param, self.ctx)
        self.assertIn(expected_error, str(context.exception))

    def test_no_validation_when_valid_fields_not_provided(self):
        """Test that no validation occurs when valid_fields is None."""
        param_type = FieldList(valid_fields=None)
        # Should not raise even with arbitrary field names
        result = param_type.convert("foo,bar,baz", self.param, self.ctx)

        self.assertEqual(result, ["foo", "bar", "baz"])

    def test_repr_without_validation(self):
        """Test string representation without validation."""
        param_type = FieldList()
        self.assertEqual(repr(param_type), "FieldList")

    def test_repr_with_validation(self):
        """Test string representation with validation."""
        valid_fields = {"id", "name", "priority"}
        param_type = FieldList(valid_fields=valid_fields)
        result = repr(param_type)

        self.assertIn("FieldList(", result)
        self.assertIn("id", result)
        self.assertIn("name", result)
        self.assertIn("priority", result)


if __name__ == "__main__":
    unittest.main()
