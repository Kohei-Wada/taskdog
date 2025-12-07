"""Tests for ValidationMessages constants."""

import pytest

from taskdog.constants.validation_messages import ValidationMessages


class TestValidationMessagesConstants:
    """Test cases for ValidationMessages static constants."""

    @pytest.mark.parametrize(
        "constant_name",
        [
            "TASK_NAME_REQUIRED",
            "PRIORITY_MUST_BE_NUMBER",
            "PRIORITY_MUST_BE_POSITIVE",
            "DURATION_MUST_BE_NUMBER",
            "DURATION_MUST_BE_POSITIVE",
            "DURATION_MAX_EXCEEDED",
            "TAG_CANNOT_BE_EMPTY",
            "TAGS_MUST_BE_UNIQUE",
        ],
    )
    def test_constant_is_non_empty_string(self, constant_name: str) -> None:
        """Test that all constants are non-empty strings."""
        value = getattr(ValidationMessages, constant_name)
        assert isinstance(value, str)
        assert len(value) > 0

    def test_task_name_required(self) -> None:
        """Test TASK_NAME_REQUIRED message content."""
        assert "name" in ValidationMessages.TASK_NAME_REQUIRED.lower()
        assert "required" in ValidationMessages.TASK_NAME_REQUIRED.lower()

    def test_priority_must_be_number(self) -> None:
        """Test PRIORITY_MUST_BE_NUMBER message content."""
        assert "priority" in ValidationMessages.PRIORITY_MUST_BE_NUMBER.lower()
        assert "number" in ValidationMessages.PRIORITY_MUST_BE_NUMBER.lower()

    def test_priority_must_be_positive(self) -> None:
        """Test PRIORITY_MUST_BE_POSITIVE message content."""
        assert "priority" in ValidationMessages.PRIORITY_MUST_BE_POSITIVE.lower()

    def test_duration_must_be_number(self) -> None:
        """Test DURATION_MUST_BE_NUMBER message content."""
        assert "duration" in ValidationMessages.DURATION_MUST_BE_NUMBER.lower()
        assert "number" in ValidationMessages.DURATION_MUST_BE_NUMBER.lower()

    def test_duration_must_be_positive(self) -> None:
        """Test DURATION_MUST_BE_POSITIVE message content."""
        assert "duration" in ValidationMessages.DURATION_MUST_BE_POSITIVE.lower()

    def test_duration_max_exceeded(self) -> None:
        """Test DURATION_MAX_EXCEEDED message content."""
        assert "duration" in ValidationMessages.DURATION_MAX_EXCEEDED.lower()
        assert "999" in ValidationMessages.DURATION_MAX_EXCEEDED

    def test_tag_cannot_be_empty(self) -> None:
        """Test TAG_CANNOT_BE_EMPTY message content."""
        assert "tag" in ValidationMessages.TAG_CANNOT_BE_EMPTY.lower()
        assert "empty" in ValidationMessages.TAG_CANNOT_BE_EMPTY.lower()

    def test_tags_must_be_unique(self) -> None:
        """Test TAGS_MUST_BE_UNIQUE message content."""
        assert "tag" in ValidationMessages.TAGS_MUST_BE_UNIQUE.lower()
        assert "unique" in ValidationMessages.TAGS_MUST_BE_UNIQUE.lower()


class TestInvalidDateFormat:
    """Test cases for invalid_date_format static method."""

    def test_formats_field_name_and_examples(self) -> None:
        """Test that field name and examples are included in message."""
        result = ValidationMessages.invalid_date_format(
            "deadline", "2025-12-31, tomorrow"
        )
        assert "deadline" in result
        assert "2025-12-31, tomorrow" in result

    def test_various_field_names(self) -> None:
        """Test with various field names."""
        field_names = ["deadline", "planned start", "planned end", "due date"]
        for field_name in field_names:
            result = ValidationMessages.invalid_date_format(field_name, "example")
            assert field_name in result

    def test_empty_field_name(self) -> None:
        """Test with empty field name."""
        result = ValidationMessages.invalid_date_format("", "example")
        assert "Invalid" in result
        assert "example" in result

    def test_empty_examples(self) -> None:
        """Test with empty examples."""
        result = ValidationMessages.invalid_date_format("deadline", "")
        assert "deadline" in result

    def test_special_characters_in_field_name(self) -> None:
        """Test with special characters in field name."""
        result = ValidationMessages.invalid_date_format("planned_start", "example")
        assert "planned_start" in result


class TestInvalidTaskId:
    """Test cases for invalid_task_id static method."""

    def test_includes_invalid_value(self) -> None:
        """Test that the invalid value is included in message."""
        result = ValidationMessages.invalid_task_id("abc")
        assert "abc" in result

    def test_indicates_must_be_number(self) -> None:
        """Test that message indicates value must be a number."""
        result = ValidationMessages.invalid_task_id("xyz")
        assert "number" in result.lower()

    def test_various_invalid_values(self) -> None:
        """Test with various invalid values."""
        invalid_values = ["abc", "1.5", "-1", "", "null", "undefined"]
        for value in invalid_values:
            result = ValidationMessages.invalid_task_id(value)
            assert value in result

    def test_special_characters(self) -> None:
        """Test with special characters in value."""
        result = ValidationMessages.invalid_task_id("<script>")
        assert "<script>" in result


class TestTaskNotFound:
    """Test cases for task_not_found static method."""

    def test_includes_task_id(self) -> None:
        """Test that the task ID is included in message."""
        result = ValidationMessages.task_not_found(123)
        assert "123" in result

    def test_indicates_not_found(self) -> None:
        """Test that message indicates task was not found."""
        result = ValidationMessages.task_not_found(1)
        assert "not found" in result.lower()

    def test_various_task_ids(self) -> None:
        """Test with various task IDs."""
        task_ids = [1, 100, 999, 0, 12345]
        for task_id in task_ids:
            result = ValidationMessages.task_not_found(task_id)
            assert str(task_id) in result

    def test_message_format_includes_hash(self) -> None:
        """Test that message includes # prefix for task ID."""
        result = ValidationMessages.task_not_found(42)
        assert "#42" in result
