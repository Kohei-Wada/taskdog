"""Tests for StatusValidator."""

from unittest.mock import Mock

import pytest

from taskdog_core.application.validators.status_validator import StatusValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
    TaskValidationError,
)


class TestStatusValidator:
    """Test cases for StatusValidator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize validator and mock repository for each test."""
        self.validator = StatusValidator()
        self.mock_repository = Mock()

    @pytest.mark.parametrize(
        "scenario,current_status,target_status",
        [
            ("pending_to_in_progress", TaskStatus.PENDING, TaskStatus.IN_PROGRESS),
            ("in_progress_to_completed", TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED),
            ("in_progress_to_pending", TaskStatus.IN_PROGRESS, TaskStatus.PENDING),
        ],
        ids=[
            "pending_to_in_progress",
            "in_progress_to_completed",
            "in_progress_to_pending",
        ],
    )
    def test_validate_successful_status_transitions(
        self, scenario, current_status, target_status
    ):
        """Test valid status transitions."""
        task = Task(id=1, name="Test", status=current_status, priority=1)
        # Should not raise
        self.validator.validate(target_status, task, self.mock_repository)

    def test_validate_pending_to_completed_raises_error(self):
        """Test that PENDING task cannot transition directly to COMPLETED."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        with pytest.raises(TaskNotStartedError) as exc_info:
            self.validator.validate(TaskStatus.COMPLETED, task, self.mock_repository)

        assert exc_info.value.task_id == 1

    @pytest.mark.parametrize(
        "scenario,current_status,target_status",
        [
            ("completed_to_in_progress", TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS),
            ("canceled_to_in_progress", TaskStatus.CANCELED, TaskStatus.IN_PROGRESS),
            ("completed_to_pending", TaskStatus.COMPLETED, TaskStatus.PENDING),
            ("canceled_to_completed", TaskStatus.CANCELED, TaskStatus.COMPLETED),
        ],
        ids=[
            "completed_to_in_progress",
            "canceled_to_in_progress",
            "completed_to_pending",
            "canceled_to_completed",
        ],
    )
    def test_validate_finished_task_transitions_raise_error(
        self, scenario, current_status, target_status
    ):
        """Test that finished tasks cannot transition to active states."""
        task = Task(id=1, name="Test", status=current_status, priority=1)

        with pytest.raises(TaskAlreadyFinishedError) as exc_info:
            self.validator.validate(target_status, task, self.mock_repository)

        assert exc_info.value.task_id == 1
        assert exc_info.value.status == current_status.name

    def test_validate_start_with_completed_dependencies_success(self):
        """Test that task with COMPLETED dependencies can be started."""
        task = Task(
            id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2]
        )

        # Mock repository to return completed dependencies
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.COMPLETED, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep1, 2: dep2}

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    @pytest.mark.parametrize(
        "scenario,dep_status",
        [
            ("pending_dependency", TaskStatus.PENDING),
            ("in_progress_dependency", TaskStatus.IN_PROGRESS),
        ],
        ids=["pending_dependency", "in_progress_dependency"],
    )
    def test_validate_start_with_unmet_dependency_raises_error(
        self, scenario, dep_status
    ):
        """Test that task with unmet dependencies cannot be started."""
        task = Task(
            id=2,
            name="Test",
            status=TaskStatus.PENDING,
            priority=1,
            depends_on=[1],
        )

        # Mock repository to return dependency with given status
        dep = Task(id=1, name="Dependency", status=dep_status, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep}

        with pytest.raises(DependencyNotMetError) as exc_info:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        assert exc_info.value.task_id == 2
        assert 1 in exc_info.value.unmet_dependencies

    def test_validate_start_with_missing_dependency_raises_error(self):
        """Test that task with missing dependency cannot be started."""
        task = Task(
            id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[999]
        )

        # Mock repository to return empty dict (dependency not found)
        self.mock_repository.get_by_ids.return_value = {}

        with pytest.raises(DependencyNotMetError) as exc_info:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        assert exc_info.value.task_id == 2
        assert 999 in exc_info.value.unmet_dependencies

    def test_validate_start_with_mixed_dependencies_raises_error(self):
        """Test that task with mix of met and unmet dependencies cannot be started."""
        task = Task(
            id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2]
        )

        # Mock repository: dep1 completed, dep2 pending
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep1, 2: dep2}

        with pytest.raises(DependencyNotMetError) as exc_info:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        assert exc_info.value.task_id == 3
        assert 2 in exc_info.value.unmet_dependencies
        assert 1 not in exc_info.value.unmet_dependencies

    def test_validate_start_with_no_dependencies_success(self):
        """Test that task with no dependencies can be started."""
        task = Task(
            id=1, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[]
        )

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    def test_validate_task_without_id_raises_error(self):
        """Test that task without ID raises TaskValidationError."""
        # Create task without ID (id=None)
        task = Task(name="Test", status=TaskStatus.PENDING, priority=1)

        with pytest.raises(TaskValidationError) as exc_info:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        assert "Task ID must not be None" in str(exc_info.value)

    @pytest.mark.parametrize(
        "scenario,current_status,expected_error",
        [
            ("pending_can_be_canceled", TaskStatus.PENDING, None),
            ("in_progress_can_be_canceled", TaskStatus.IN_PROGRESS, None),
            (
                "completed_cannot_be_canceled",
                TaskStatus.COMPLETED,
                TaskAlreadyFinishedError,
            ),
        ],
        ids=[
            "pending_can_be_canceled",
            "in_progress_can_be_canceled",
            "completed_cannot_be_canceled",
        ],
    )
    def test_validate_cancel_transitions(
        self, scenario, current_status, expected_error
    ):
        """Test cancel transitions for different task states."""
        task = Task(id=1, name="Test", status=current_status, priority=1)

        if expected_error:
            with pytest.raises(expected_error) as exc_info:
                self.validator.validate(TaskStatus.CANCELED, task, self.mock_repository)
            assert exc_info.value.task_id == 1
            assert exc_info.value.status == current_status.name
        else:
            # Should not raise
            self.validator.validate(TaskStatus.CANCELED, task, self.mock_repository)

    @pytest.mark.parametrize(
        "scenario,current_status,target_status,expected_message_prefix",
        [
            (
                "start_operation",
                TaskStatus.COMPLETED,
                TaskStatus.IN_PROGRESS,
                "Cannot start task",
            ),
            (
                "complete_operation",
                TaskStatus.COMPLETED,
                TaskStatus.COMPLETED,
                "Cannot complete task",
            ),
            (
                "cancel_operation",
                TaskStatus.COMPLETED,
                TaskStatus.CANCELED,
                "Cannot cancel task",
            ),
            (
                "pause_operation",
                TaskStatus.CANCELED,
                TaskStatus.PENDING,
                "Cannot pause task",
            ),
        ],
        ids=[
            "start_operation",
            "complete_operation",
            "cancel_operation",
            "pause_operation",
        ],
    )
    def test_error_message_contains_correct_operation(
        self, scenario, current_status, target_status, expected_message_prefix
    ):
        """Test that error message contains the correct operation verb for each status transition."""
        task = Task(id=1, name="Test", status=current_status, priority=1)

        with pytest.raises(TaskAlreadyFinishedError) as exc_info:
            self.validator.validate(target_status, task, self.mock_repository)

        error_message = str(exc_info.value)
        assert expected_message_prefix in error_message
        assert f"task is already {current_status.name}" in error_message
