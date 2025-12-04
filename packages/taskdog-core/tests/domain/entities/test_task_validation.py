"""Tests for Task entity invariant validation."""

import pytest

from taskdog_core.domain.constants import (
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_TASK,
    MAX_TASK_NAME_LENGTH,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestTaskValidation:
    """Test Task entity invariant validation in __post_init__."""

    @pytest.fixture
    def mapper(self):
        """Create TaskDbMapper instance."""
        return TaskDbMapper()

    @pytest.mark.parametrize(
        "task_kwargs,attr_name,expected_value",
        [
            ({"name": "Test Task", "priority": 5}, "name", "Test Task"),
            ({"name": "Test Task", "priority": 5}, "priority", 5),
            (
                {"name": "Test Task", "priority": 5, "estimated_duration": 10.0},
                "estimated_duration",
                10.0,
            ),
            (
                {"name": "Test Task", "priority": 5, "tags": ["work", "urgent"]},
                "tags",
                ["work", "urgent"],
            ),
            (
                {"name": "Test Task", "priority": 5, "estimated_duration": None},
                "estimated_duration",
                None,
            ),
        ],
        ids=[
            "basic_task_name",
            "basic_task_priority",
            "with_estimated_duration",
            "with_tags",
            "with_none_estimated_duration",
        ],
    )
    def test_valid_task_creation(self, task_kwargs, attr_name, expected_value):
        """Test creating tasks with valid values."""
        task = Task(**task_kwargs)
        assert getattr(task, attr_name) == expected_value

    @pytest.mark.parametrize(
        "tags,expected_error",
        [
            (["work", "", "urgent"], "Tag cannot be empty"),
            (["work", "urgent", "work"], "Tags must be unique"),
        ],
        ids=["empty_tag", "duplicate_tags"],
    )
    def test_invalid_tags(self, tags, expected_error):
        """Test that invalid tags raise TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            Task(name="Test Task", priority=5, tags=tags)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "name,expected_error",
        [
            ("", "Task name cannot be empty"),
            ("   ", "Task name cannot be empty"),
        ],
        ids=["empty_name", "whitespace_only_name"],
    )
    def test_invalid_name(self, name, expected_error):
        """Test that invalid task names raise TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            Task(name=name, priority=5)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "priority,expected_error",
        [
            (0, "Priority must be greater than 0"),
            (-1, "Priority must be greater than 0"),
        ],
        ids=["zero_priority", "negative_priority"],
    )
    def test_invalid_priority(self, priority, expected_error):
        """Test that invalid priority values raise TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            Task(name="Test Task", priority=priority)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "duration,expected_error",
        [
            (0.0, "Estimated duration must be greater than 0"),
            (-5.0, "Estimated duration must be greater than 0"),
        ],
        ids=["zero_duration", "negative_duration"],
    )
    def test_invalid_estimated_duration(self, duration, expected_error):
        """Test that invalid estimated_duration values raise TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            Task(name="Test Task", priority=5, estimated_duration=duration)
        assert expected_error in str(exc_info.value)

    def test_from_dict_with_valid_data(self, mapper):
        """Test that from_dict works with valid data."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": "PENDING",
            "estimated_duration": 10.0,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }
        task = mapper.from_dict(data)
        assert task.id == 1
        assert task.name == "Test Task"
        assert task.priority == 5
        assert task.status == TaskStatus.PENDING
        assert task.estimated_duration == 10.0

    @pytest.mark.parametrize(
        "task_dict,expected_error",
        [
            (
                {"id": 1, "name": "", "priority": 5, "status": "PENDING"},
                "Task name cannot be empty",
            ),
            (
                {"id": 1, "name": "Test Task", "priority": 0, "status": "PENDING"},
                "Priority must be greater than 0",
            ),
            (
                {"id": 1, "name": "Test Task", "priority": -100, "status": "PENDING"},
                "Priority must be greater than 0",
            ),
            (
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": 0.0,
                },
                "Estimated duration must be greater than 0",
            ),
            (
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": -5.0,
                },
                "Estimated duration must be greater than 0",
            ),
        ],
        ids=[
            "empty_name",
            "zero_priority",
            "negative_priority",
            "zero_estimated_duration",
            "negative_estimated_duration",
        ],
    )
    def test_from_dict_validation_errors(self, mapper, task_dict, expected_error):
        """Test that from_dict raises validation errors for invalid fields."""
        # Add required timestamp fields
        data = {
            **task_dict,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }
        with pytest.raises(TaskValidationError) as exc_info:
            mapper.from_dict(data)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "name,should_raise",
        [
            ("a" * MAX_TASK_NAME_LENGTH, False),
            ("a" * (MAX_TASK_NAME_LENGTH + 1), True),
        ],
        ids=["name_at_limit", "name_over_limit"],
    )
    def test_name_length_validation(self, name, should_raise):
        """Test task name length validation at boundary values."""
        if should_raise:
            with pytest.raises(TaskValidationError) as exc_info:
                Task(name=name, priority=5)
            assert f"cannot exceed {MAX_TASK_NAME_LENGTH}" in str(exc_info.value)
        else:
            task = Task(name=name, priority=5)
            assert task.name == name

    @pytest.mark.parametrize(
        "tag,should_raise",
        [
            ("a" * MAX_TAG_LENGTH, False),
            ("a" * (MAX_TAG_LENGTH + 1), True),
        ],
        ids=["tag_at_limit", "tag_over_limit"],
    )
    def test_tag_length_validation(self, tag, should_raise):
        """Test individual tag length validation at boundary values."""
        if should_raise:
            with pytest.raises(TaskValidationError) as exc_info:
                Task(name="Test Task", priority=5, tags=[tag])
            assert f"cannot exceed {MAX_TAG_LENGTH}" in str(exc_info.value)
        else:
            task = Task(name="Test Task", priority=5, tags=[tag])
            assert task.tags == [tag]

    @pytest.mark.parametrize(
        "tag_count,should_raise",
        [
            (MAX_TAGS_PER_TASK, False),
            (MAX_TAGS_PER_TASK + 1, True),
        ],
        ids=["tags_at_limit", "tags_over_limit"],
    )
    def test_tags_count_validation(self, tag_count, should_raise):
        """Test tags count validation at boundary values."""
        tags = [f"tag{i}" for i in range(tag_count)]
        if should_raise:
            with pytest.raises(TaskValidationError) as exc_info:
                Task(name="Test Task", priority=5, tags=tags)
            assert f"more than {MAX_TAGS_PER_TASK}" in str(exc_info.value)
        else:
            task = Task(name="Test Task", priority=5, tags=tags)
            assert len(task.tags) == tag_count
