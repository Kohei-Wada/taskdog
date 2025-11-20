"""Tests for Pydantic request models."""

import unittest
from datetime import date, datetime

from parameterized import parameterized
from pydantic import ValidationError

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.api.models.requests import (
    AddDependencyRequest,
    CreateTaskRequest,
    LogHoursRequest,
    OptimizeScheduleRequest,
    SetTaskTagsRequest,
    TaskFilterParams,
    TaskSortParams,
    UpdateNotesRequest,
    UpdateTaskRequest,
)


class TestCreateTaskRequest(unittest.TestCase):
    """Test cases for CreateTaskRequest model."""

    def test_valid_minimal_request(self):
        """Test creating request with minimal required fields."""
        # Act
        request = CreateTaskRequest(name="Test Task")

        # Assert
        self.assertEqual(request.name, "Test Task")
        self.assertIsNone(request.priority)
        self.assertIsNone(request.planned_start)
        self.assertIsNone(request.deadline)
        self.assertEqual(request.is_fixed, False)

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
        self.assertEqual(request.name, "Test Task")
        self.assertEqual(request.priority, 1)
        self.assertEqual(request.planned_start, now)
        self.assertEqual(request.estimated_duration, 8.0)
        self.assertEqual(request.is_fixed, True)
        self.assertEqual(request.tags, ["backend", "api"])

    @parameterized.expand(
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
        ]
    )
    def test_create_task_request_validation_errors(
        self, _scenario, kwargs, expected_error
    ):
        """Test CreateTaskRequest validation errors."""
        with self.assertRaises(ValidationError) as context:
            CreateTaskRequest(**kwargs)
        self.assertIn(expected_error, str(context.exception))

    def test_valid_single_tag(self):
        """Test creating request with single tag."""
        # Act
        request = CreateTaskRequest(name="Test", tags=["backend"])

        # Assert
        self.assertEqual(request.tags, ["backend"])


class TestUpdateTaskRequest(unittest.TestCase):
    """Test cases for UpdateTaskRequest model."""

    def test_valid_empty_update(self):
        """Test creating update request with no fields."""
        # Act
        request = UpdateTaskRequest()

        # Assert
        self.assertIsNone(request.name)
        self.assertIsNone(request.priority)
        self.assertIsNone(request.status)

    def test_valid_partial_update(self):
        """Test updating only some fields."""
        # Act
        request = UpdateTaskRequest(name="New Name", priority=2)

        # Assert
        self.assertEqual(request.name, "New Name")
        self.assertEqual(request.priority, 2)
        self.assertIsNone(request.status)

    def test_valid_status_update(self):
        """Test updating task status."""
        # Act
        request = UpdateTaskRequest(status=TaskStatus.IN_PROGRESS)

        # Assert
        self.assertEqual(request.status, TaskStatus.IN_PROGRESS)

    @parameterized.expand(
        [
            ("empty_name", {"name": ""}, "name"),
            ("zero_priority", {"priority": 0}, "priority"),
            ("empty_tag", {"tags": ["valid", ""]}, "Tags must be non-empty"),
        ]
    )
    def test_update_task_request_validation_errors(
        self, _scenario, kwargs, expected_error
    ):
        """Test UpdateTaskRequest validation errors."""
        with self.assertRaises(ValidationError) as context:
            UpdateTaskRequest(**kwargs)
        self.assertIn(expected_error, str(context.exception))


class TestAddDependencyRequest(unittest.TestCase):
    """Test cases for AddDependencyRequest model."""

    def test_valid_request(self):
        """Test creating valid dependency request."""
        # Act
        request = AddDependencyRequest(depends_on_id=123)

        # Assert
        self.assertEqual(request.depends_on_id, 123)

    def test_missing_depends_on_id(self):
        """Test that depends_on_id is required."""
        # Act & Assert
        with self.assertRaises(ValidationError):
            AddDependencyRequest()


class TestSetTaskTagsRequest(unittest.TestCase):
    """Test cases for SetTaskTagsRequest model."""

    def test_valid_request(self):
        """Test creating valid tags request."""
        # Act
        request = SetTaskTagsRequest(tags=["backend", "api"])

        # Assert
        self.assertEqual(request.tags, ["backend", "api"])

    @parameterized.expand(
        [
            ("empty_tag", {"tags": ["valid", ""]}, "Tags must be non-empty"),
            ("duplicate_tags", {"tags": ["tag1", "tag1"]}, "Tags must be unique"),
        ]
    )
    def test_set_tags_request_validation_errors(
        self, _scenario, kwargs, expected_error
    ):
        """Test SetTaskTagsRequest validation errors."""
        with self.assertRaises(ValidationError) as context:
            SetTaskTagsRequest(**kwargs)
        self.assertIn(expected_error, str(context.exception))

    def test_valid_empty_list(self):
        """Test creating request with empty tag list."""
        # Act
        request = SetTaskTagsRequest(tags=[])

        # Assert
        self.assertEqual(request.tags, [])


class TestLogHoursRequest(unittest.TestCase):
    """Test cases for LogHoursRequest model."""

    def test_valid_request_with_date(self):
        """Test creating valid log hours request with date."""
        # Arrange
        today = date.today()

        # Act
        request = LogHoursRequest(hours=8.0, date=today)

        # Assert
        self.assertEqual(request.hours, 8.0)
        self.assertEqual(request.date, today)

    def test_valid_request_without_date(self):
        """Test creating valid log hours request without date."""
        # Act
        request = LogHoursRequest(hours=4.5)

        # Assert
        self.assertEqual(request.hours, 4.5)
        self.assertIsNone(request.date)

    @parameterized.expand(
        [
            ("zero_hours", {"hours": 0.0}, "hours"),
            ("negative_hours", {"hours": -1.0}, "hours"),
        ]
    )
    def test_log_hours_request_validation_errors(
        self, _scenario, kwargs, expected_error
    ):
        """Test LogHoursRequest validation errors."""
        with self.assertRaises(ValidationError) as context:
            LogHoursRequest(**kwargs)
        self.assertIn(expected_error, str(context.exception).lower())

    def test_missing_hours(self):
        """Test that hours field is required."""
        # Act & Assert
        with self.assertRaises(ValidationError):
            LogHoursRequest()


class TestOptimizeScheduleRequest(unittest.TestCase):
    """Test cases for OptimizeScheduleRequest model."""

    def test_valid_minimal_request(self):
        """Test creating request with minimal required fields."""
        # Act
        request = OptimizeScheduleRequest(algorithm="greedy")

        # Assert
        self.assertEqual(request.algorithm, "greedy")
        self.assertIsNone(request.start_date)
        self.assertIsNone(request.max_hours_per_day)
        self.assertEqual(request.force_override, True)

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
        self.assertEqual(request.algorithm, "balanced")
        self.assertEqual(request.start_date, now)
        self.assertEqual(request.max_hours_per_day, 8.0)
        self.assertEqual(request.force_override, False)

    @parameterized.expand(
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
        ]
    )
    def test_optimize_schedule_request_validation_errors(
        self, _scenario, kwargs, expected_error
    ):
        """Test OptimizeScheduleRequest validation errors."""
        with self.assertRaises(ValidationError) as context:
            OptimizeScheduleRequest(**kwargs)
        self.assertIn(expected_error, str(context.exception).lower())

    def test_missing_algorithm(self):
        """Test that algorithm field is required."""
        # Act & Assert
        with self.assertRaises(ValidationError):
            OptimizeScheduleRequest()


class TestTaskFilterParams(unittest.TestCase):
    """Test cases for TaskFilterParams model."""

    def test_valid_default_params(self):
        """Test creating filter params with defaults."""
        # Act
        params = TaskFilterParams()

        # Assert
        self.assertEqual(params.all, False)
        self.assertIsNone(params.status)
        self.assertIsNone(params.tags)
        self.assertIsNone(params.start_date)
        self.assertIsNone(params.end_date)

    def test_valid_full_params(self):
        """Test creating filter params with all fields."""
        # Arrange
        today = date.today()

        # Act
        params = TaskFilterParams(
            all=True,
            status=TaskStatus.PENDING,
            tags=["backend", "api"],
            start_date=today,
            end_date=today,
        )

        # Assert
        self.assertEqual(params.all, True)
        self.assertEqual(params.status, TaskStatus.PENDING)
        self.assertEqual(params.tags, ["backend", "api"])
        self.assertEqual(params.start_date, today)
        self.assertEqual(params.end_date, today)

    def test_valid_status_filter(self):
        """Test filtering by status."""
        # Act
        params = TaskFilterParams(status=TaskStatus.COMPLETED)

        # Assert
        self.assertEqual(params.status, TaskStatus.COMPLETED)


class TestTaskSortParams(unittest.TestCase):
    """Test cases for TaskSortParams model."""

    def test_valid_default_params(self):
        """Test creating sort params with defaults."""
        # Act
        params = TaskSortParams()

        # Assert
        self.assertEqual(params.sort, "id")
        self.assertEqual(params.reverse, False)

    def test_valid_custom_sort(self):
        """Test creating sort params with custom field."""
        # Act
        params = TaskSortParams(sort="deadline", reverse=True)

        # Assert
        self.assertEqual(params.sort, "deadline")
        self.assertEqual(params.reverse, True)


class TestUpdateNotesRequest(unittest.TestCase):
    """Test cases for UpdateNotesRequest model."""

    def test_valid_request_with_content(self):
        """Test creating valid notes request with content."""
        # Act
        request = UpdateNotesRequest(content="# Test Notes\n\nSome content.")

        # Assert
        self.assertEqual(request.content, "# Test Notes\n\nSome content.")

    def test_valid_request_with_empty_content(self):
        """Test creating valid notes request with empty content."""
        # Act
        request = UpdateNotesRequest(content="")

        # Assert
        self.assertEqual(request.content, "")

    def test_missing_content(self):
        """Test that content field is required."""
        # Act & Assert
        with self.assertRaises(ValidationError):
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
        self.assertEqual(request.content, markdown)


if __name__ == "__main__":
    unittest.main()
