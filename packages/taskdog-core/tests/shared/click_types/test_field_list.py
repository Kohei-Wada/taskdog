"""Tests for FieldList Click type."""

import unittest
from unittest.mock import Mock

import click

from taskdog_core.shared.click_types.field_list import FieldList


class TestFieldList(unittest.TestCase):
    """Test cases for FieldList Click type."""

    def setUp(self):
        """Set up test fixtures."""
        self.param = Mock()
        self.ctx = Mock()

    def test_convert_single_field(self):
        """Test conversion of single field."""
        param_type = FieldList()
        result = param_type.convert("id", self.param, self.ctx)

        self.assertEqual(result, ["id"])

    def test_convert_multiple_fields(self):
        """Test conversion of multiple comma-separated fields."""
        param_type = FieldList()
        result = param_type.convert("id,name,priority", self.param, self.ctx)

        self.assertEqual(result, ["id", "name", "priority"])

    def test_convert_with_whitespace(self):
        """Test that whitespace around fields is stripped."""
        param_type = FieldList()
        result = param_type.convert("id, name , priority", self.param, self.ctx)

        self.assertEqual(result, ["id", "name", "priority"])

    def test_convert_none_returns_none(self):
        """Test that None input returns None."""
        param_type = FieldList()
        result = param_type.convert(None, self.param, self.ctx)

        self.assertIsNone(result)

    def test_convert_empty_string_returns_none(self):
        """Test that empty string returns None."""
        param_type = FieldList()
        result = param_type.convert("", self.param, self.ctx)

        self.assertIsNone(result)

    def test_convert_whitespace_only_returns_none(self):
        """Test that whitespace-only string returns None."""
        param_type = FieldList()
        result = param_type.convert("   ", self.param, self.ctx)

        self.assertIsNone(result)

    def test_validation_with_valid_fields(self):
        """Test that valid fields pass validation."""
        valid_fields = {"id", "name", "priority", "status"}
        param_type = FieldList(valid_fields=valid_fields)
        result = param_type.convert("id,name,priority", self.param, self.ctx)

        self.assertEqual(result, ["id", "name", "priority"])

    def test_validation_rejects_invalid_fields(self):
        """Test that invalid fields are rejected."""
        valid_fields = {"id", "name", "priority"}
        param_type = FieldList(valid_fields=valid_fields)

        with self.assertRaises(click.exceptions.BadParameter) as context:
            param_type.convert("id,invalid,name", self.param, self.ctx)

        error_message = str(context.exception)
        self.assertIn("Invalid field(s): invalid", error_message)
        self.assertIn("Valid fields are:", error_message)
        self.assertIn("id", error_message)
        self.assertIn("name", error_message)
        self.assertIn("priority", error_message)

    def test_validation_rejects_multiple_invalid_fields(self):
        """Test that multiple invalid fields are reported."""
        valid_fields = {"id", "name"}
        param_type = FieldList(valid_fields=valid_fields)

        with self.assertRaises(click.exceptions.BadParameter) as context:
            param_type.convert("id,invalid1,invalid2,name", self.param, self.ctx)

        error_message = str(context.exception)
        self.assertIn("Invalid field(s):", error_message)
        self.assertIn("invalid1", error_message)
        self.assertIn("invalid2", error_message)

    def test_validation_with_all_invalid_fields(self):
        """Test validation when all fields are invalid."""
        valid_fields = {"id", "name"}
        param_type = FieldList(valid_fields=valid_fields)

        with self.assertRaises(click.exceptions.BadParameter) as context:
            param_type.convert("foo,bar", self.param, self.ctx)

        error_message = str(context.exception)
        self.assertIn("Invalid field(s): foo, bar", error_message)

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
