"""Tests for FieldList Click type."""

from unittest.mock import Mock

import click
import pytest

from taskdog.shared.click_types.field_list import FieldList


class TestFieldList:
    """Test cases for FieldList Click type."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.param = Mock()
        self.ctx = Mock()

    @pytest.mark.parametrize(
        "input_str,expected_result",
        [
            ("id", ["id"]),
            ("id,name,priority", ["id", "name", "priority"]),
            ("id, name , priority", ["id", "name", "priority"]),
            (None, None),
            ("", None),
            ("   ", None),
        ],
        ids=[
            "single_field",
            "multiple_fields",
            "with_whitespace",
            "none_input",
            "empty_string",
            "whitespace_only",
        ],
    )
    def test_convert(self, input_str, expected_result):
        """Test FieldList conversion with various inputs."""
        param_type = FieldList()
        result = param_type.convert(input_str, self.param, self.ctx)
        assert result == expected_result

    def test_validation_with_valid_fields(self):
        """Test that valid fields pass validation."""
        valid_fields = {"id", "name", "priority", "status"}
        param_type = FieldList(valid_fields=valid_fields)
        result = param_type.convert("id,name,priority", self.param, self.ctx)

        assert result == ["id", "name", "priority"]

    @pytest.mark.parametrize(
        "valid_fields,input_str,expected_error",
        [
            (
                {"id", "name", "priority"},
                "id,invalid,name",
                "Invalid field(s): invalid",
            ),
            (
                {"id", "name"},
                "id,invalid1,invalid2,name",
                "Invalid field(s):",
            ),
            ({"id", "name"}, "foo,bar", "Invalid field(s): foo, bar"),
        ],
        ids=["single_invalid", "multiple_invalid", "all_invalid"],
    )
    def test_validation_errors(self, valid_fields, input_str, expected_error):
        """Test FieldList validation errors."""
        param_type = FieldList(valid_fields=valid_fields)
        with pytest.raises(click.exceptions.BadParameter) as exc_info:
            param_type.convert(input_str, self.param, self.ctx)
        assert expected_error in str(exc_info.value)

    def test_no_validation_when_valid_fields_not_provided(self):
        """Test that no validation occurs when valid_fields is None."""
        param_type = FieldList(valid_fields=None)
        # Should not raise even with arbitrary field names
        result = param_type.convert("foo,bar,baz", self.param, self.ctx)

        assert result == ["foo", "bar", "baz"]

    def test_repr_without_validation(self):
        """Test string representation without validation."""
        param_type = FieldList()
        assert repr(param_type) == "FieldList"

    def test_repr_with_validation(self):
        """Test string representation with validation."""
        valid_fields = {"id", "name", "priority"}
        param_type = FieldList(valid_fields=valid_fields)
        result = repr(param_type)

        assert "FieldList(" in result
        assert "id" in result
        assert "name" in result
        assert "priority" in result
