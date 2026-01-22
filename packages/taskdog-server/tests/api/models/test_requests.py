"""Tests for Pydantic request models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.api.models.requests import (
    AddDependencyRequest,
    CreateTaskRequest,
    OptimizeScheduleRequest,
    SetTaskTagsRequest,
    UpdateNotesRequest,
    UpdateTaskRequest,
)


class TestCreateTaskRequest:
    """Test cases for CreateTaskRequest model."""

    def test_valid_minimal_request(self):
        """Test creating request with minimal required fields."""
        # Act
        request = CreateTaskRequest(name="Test Task")

        # Assert
        assert request.name == "Test Task"
        assert request.priority is None
        assert request.planned_start is None
        assert request.deadline is None
        assert request.is_fixed is False

    def test_valid_full_request(self):
        """Test creating request with all fields."""
        # Arrange
        now = datetime.now()

        # Act
        request = CreateTaskRequest(
            name="Test Task",
            priority=1,
            planned_start=now,
            planned_end=now,
            deadline=now,
            estimated_duration=8.0,
            is_fixed=True,
            tags=["backend", "api"],
        )

        # Assert
        assert request.name == "Test Task"
        assert request.priority == 1
        assert request.planned_start == now
        assert request.estimated_duration == 8.0
        assert request.is_fixed is True
        assert request.tags == ["backend", "api"]

    @pytest.mark.parametrize(
        "scenario,kwargs,expected_error",
        [
            ("empty_name", {"name": ""}, "name"),
            ("zero_priority", {"name": "Test", "priority": 0}, "priority"),
            ("negative_priority", {"name": "Test", "priority": -1}, "priority"),
            (
                "zero_duration",
                {"name": "Test", "estimated_duration": 0.0},
                "estimated_duration",
            ),
            (
                "empty_tag",
                {"name": "Test", "tags": ["valid", ""]},
                "Tags must be non-empty",
            ),
            (
                "duplicate_tags",
                {"name": "Test", "tags": ["tag1", "tag1"]},
                "Tags must be unique",
            ),
        ],
    )
    def test_create_task_request_validation_errors(
        self, scenario, kwargs, expected_error
    ):
        """Test CreateTaskRequest validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTaskRequest(**kwargs)
        assert expected_error in str(exc_info.value)

    def test_valid_single_tag(self):
        """Test creating request with single tag."""
        # Act
        request = CreateTaskRequest(name="Test", tags=["backend"])

        # Assert
        assert request.tags == ["backend"]


class TestUpdateTaskRequest:
    """Test cases for UpdateTaskRequest model."""

    def test_valid_empty_update(self):
        """Test creating update request with no fields."""
        # Act
        request = UpdateTaskRequest()

        # Assert
        assert request.name is None
        assert request.priority is None
        assert request.status is None

    def test_valid_partial_update(self):
        """Test updating only some fields."""
        # Act
        request = UpdateTaskRequest(name="New Name", priority=2)

        # Assert
        assert request.name == "New Name"
        assert request.priority == 2
        assert request.status is None

    def test_valid_status_update(self):
        """Test updating task status."""
        # Act
        request = UpdateTaskRequest(status=TaskStatus.IN_PROGRESS)

        # Assert
        assert request.status == TaskStatus.IN_PROGRESS

    @pytest.mark.parametrize(
        "scenario,kwargs,expected_error",
        [
            ("empty_name", {"name": ""}, "name"),
            ("zero_priority", {"priority": 0}, "priority"),
            ("empty_tag", {"tags": ["valid", ""]}, "Tags must be non-empty"),
        ],
    )
    def test_update_task_request_validation_errors(
        self, scenario, kwargs, expected_error
    ):
        """Test UpdateTaskRequest validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateTaskRequest(**kwargs)
        assert expected_error in str(exc_info.value)


class TestAddDependencyRequest:
    """Test cases for AddDependencyRequest model."""

    def test_valid_request(self):
        """Test creating valid dependency request."""
        # Act
        request = AddDependencyRequest(depends_on_id=123)

        # Assert
        assert request.depends_on_id == 123

    def test_missing_depends_on_id(self):
        """Test that depends_on_id is required."""
        # Act & Assert
        with pytest.raises(ValidationError):
            AddDependencyRequest()


class TestSetTaskTagsRequest:
    """Test cases for SetTaskTagsRequest model."""

    def test_valid_request(self):
        """Test creating valid tags request."""
        # Act
        request = SetTaskTagsRequest(tags=["backend", "api"])

        # Assert
        assert request.tags == ["backend", "api"]

    @pytest.mark.parametrize(
        "scenario,kwargs,expected_error",
        [
            ("empty_tag", {"tags": ["valid", ""]}, "Tags must be non-empty"),
            ("duplicate_tags", {"tags": ["tag1", "tag1"]}, "Tags must be unique"),
        ],
    )
    def test_set_tags_request_validation_errors(self, scenario, kwargs, expected_error):
        """Test SetTaskTagsRequest validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            SetTaskTagsRequest(**kwargs)
        assert expected_error in str(exc_info.value)

    def test_valid_empty_list(self):
        """Test creating request with empty tag list."""
        # Act
        request = SetTaskTagsRequest(tags=[])

        # Assert
        assert request.tags == []


class TestOptimizeScheduleRequest:
    """Test cases for OptimizeScheduleRequest model."""

    def test_valid_minimal_request(self):
        """Test creating request with minimal required fields."""
        # Act
        request = OptimizeScheduleRequest(algorithm="greedy", max_hours_per_day=6.0)

        # Assert
        assert request.algorithm == "greedy"
        assert request.start_date is None
        assert request.max_hours_per_day == 6.0
        assert request.force_override is True

    def test_valid_full_request(self):
        """Test creating request with all fields."""
        # Arrange
        now = datetime.now()

        # Act
        request = OptimizeScheduleRequest(
            algorithm="balanced",
            start_date=now,
            max_hours_per_day=8.0,
            force_override=False,
        )

        # Assert
        assert request.algorithm == "balanced"
        assert request.start_date == now
        assert request.max_hours_per_day == 8.0
        assert request.force_override is False

    @pytest.mark.parametrize(
        "scenario,kwargs,expected_error",
        [
            (
                "zero_max_hours",
                {"algorithm": "greedy", "max_hours_per_day": 0.0},
                "max_hours_per_day",
            ),
            (
                "excessive_max_hours",
                {"algorithm": "greedy", "max_hours_per_day": 25.0},
                "max_hours_per_day",
            ),
        ],
    )
    def test_optimize_schedule_request_validation_errors(
        self, scenario, kwargs, expected_error
    ):
        """Test OptimizeScheduleRequest validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            OptimizeScheduleRequest(**kwargs)
        assert expected_error in str(exc_info.value).lower()

    def test_missing_algorithm(self):
        """Test that algorithm field is required."""
        # Act & Assert
        with pytest.raises(ValidationError):
            OptimizeScheduleRequest()


class TestUpdateNotesRequest:
    """Test cases for UpdateNotesRequest model."""

    def test_valid_request_with_content(self):
        """Test creating valid notes request with content."""
        # Act
        request = UpdateNotesRequest(content="# Test Notes\n\nSome content.")

        # Assert
        assert request.content == "# Test Notes\n\nSome content."

    def test_valid_request_with_empty_content(self):
        """Test creating valid notes request with empty content."""
        # Act
        request = UpdateNotesRequest(content="")

        # Assert
        assert request.content == ""

    def test_missing_content(self):
        """Test that content field is required."""
        # Act & Assert
        with pytest.raises(ValidationError):
            UpdateNotesRequest()

    def test_valid_markdown_content(self):
        """Test creating request with markdown formatted content."""
        # Arrange
        markdown = """# Title

## Subtitle

- Item 1
- Item 2
"""
        # Act
        request = UpdateNotesRequest(content=markdown)

        # Assert
        assert request.content == markdown
