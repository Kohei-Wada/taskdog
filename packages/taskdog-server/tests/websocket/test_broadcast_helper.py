"""Tests for BroadcastHelper."""

import unittest
from unittest.mock import MagicMock, call

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.websocket.broadcast_helper import BroadcastHelper
from taskdog_server.websocket.broadcaster import (
    broadcast_schedule_optimized,
    broadcast_task_created,
    broadcast_task_deleted,
    broadcast_task_notes_updated,
    broadcast_task_status_changed,
    broadcast_task_updated,
)
from taskdog_server.websocket.connection_manager import ConnectionManager


class TestBroadcastHelper(unittest.TestCase):
    """Test cases for BroadcastHelper."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_manager = MagicMock(spec=ConnectionManager)
        self.mock_background_tasks = MagicMock()
        self.helper = BroadcastHelper(self.mock_manager, self.mock_background_tasks)

    def _create_task_output(
        self,
        task_id: int = 1,
        name: str = "Test Task",
        status: TaskStatus = TaskStatus.PENDING,
    ) -> TaskOperationOutput:
        """Create a TaskOperationOutput for testing."""
        return TaskOperationOutput(
            id=task_id,
            name=name,
            status=status,
            priority=1,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )

    def test_task_created_schedules_broadcast(self):
        """Test task_created schedules broadcast_task_created."""
        # Arrange
        task = self._create_task_output()
        exclude_client_id = "client-1"

        # Act
        self.helper.task_created(task, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_created, self.mock_manager, task, exclude_client_id
        )

    def test_task_created_without_exclude_client(self):
        """Test task_created with no exclude client."""
        # Arrange
        task = self._create_task_output()

        # Act
        self.helper.task_created(task)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_created, self.mock_manager, task, None
        )

    def test_task_updated_schedules_broadcast(self):
        """Test task_updated schedules broadcast_task_updated."""
        # Arrange
        task = self._create_task_output()
        fields = ["name", "priority"]
        exclude_client_id = "client-2"

        # Act
        self.helper.task_updated(task, fields, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_updated, self.mock_manager, task, fields, exclude_client_id
        )

    def test_task_updated_with_single_field(self):
        """Test task_updated with a single field."""
        # Arrange
        task = self._create_task_output()
        fields = ["is_archived"]

        # Act
        self.helper.task_updated(task, fields)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_updated, self.mock_manager, task, fields, None
        )

    def test_task_deleted_schedules_broadcast(self):
        """Test task_deleted schedules broadcast_task_deleted."""
        # Arrange
        task_id = 123
        task_name = "Deleted Task"
        exclude_client_id = "client-3"

        # Act
        self.helper.task_deleted(task_id, task_name, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_deleted,
            self.mock_manager,
            task_id,
            task_name,
            exclude_client_id,
        )

    def test_task_deleted_without_exclude_client(self):
        """Test task_deleted with no exclude client."""
        # Arrange
        task_id = 456
        task_name = "Another Task"

        # Act
        self.helper.task_deleted(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_deleted, self.mock_manager, task_id, task_name, None
        )

    def test_task_status_changed_schedules_broadcast(self):
        """Test task_status_changed schedules broadcast_task_status_changed."""
        # Arrange
        task = self._create_task_output(status=TaskStatus.IN_PROGRESS)
        old_status = "PENDING"
        exclude_client_id = "client-4"

        # Act
        self.helper.task_status_changed(task, old_status, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_status_changed,
            self.mock_manager,
            task,
            old_status,
            exclude_client_id,
        )

    def test_task_status_changed_with_different_statuses(self):
        """Test task_status_changed with various status transitions."""
        # Arrange
        task = self._create_task_output(status=TaskStatus.COMPLETED)
        old_status = "IN_PROGRESS"

        # Act
        self.helper.task_status_changed(task, old_status)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_status_changed,
            self.mock_manager,
            task,
            old_status,
            None,
        )

    def test_task_notes_updated_schedules_broadcast(self):
        """Test task_notes_updated schedules broadcast_task_notes_updated."""
        # Arrange
        task_id = 789
        task_name = "Task with Notes"
        exclude_client_id = "client-5"

        # Act
        self.helper.task_notes_updated(task_id, task_name, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_notes_updated,
            self.mock_manager,
            task_id,
            task_name,
            exclude_client_id,
        )

    def test_task_notes_updated_without_exclude_client(self):
        """Test task_notes_updated with no exclude client."""
        # Arrange
        task_id = 101
        task_name = "Notes Task"

        # Act
        self.helper.task_notes_updated(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_task_notes_updated,
            self.mock_manager,
            task_id,
            task_name,
            None,
        )

    def test_schedule_optimized_schedules_broadcast(self):
        """Test schedule_optimized schedules broadcast_schedule_optimized."""
        # Arrange
        scheduled_count = 5
        failed_count = 2
        algorithm = "greedy"
        exclude_client_id = "client-6"

        # Act
        self.helper.schedule_optimized(
            scheduled_count, failed_count, algorithm, exclude_client_id
        )

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            broadcast_schedule_optimized,
            self.mock_manager,
            scheduled_count,
            failed_count,
            algorithm,
            exclude_client_id,
        )

    def test_schedule_optimized_with_different_algorithms(self):
        """Test schedule_optimized with various algorithms."""
        algorithms = ["greedy", "balanced", "backward", "priority_first", "genetic"]

        for algorithm in algorithms:
            # Reset mock for each iteration
            self.mock_background_tasks.reset_mock()

            # Act
            self.helper.schedule_optimized(10, 0, algorithm)

            # Assert
            self.mock_background_tasks.add_task.assert_called_once_with(
                broadcast_schedule_optimized,
                self.mock_manager,
                10,
                0,
                algorithm,
                None,
            )

    def test_multiple_broadcasts_in_sequence(self):
        """Test multiple broadcast calls are scheduled correctly."""
        # Arrange
        task1 = self._create_task_output(task_id=1, name="Task 1")
        task2 = self._create_task_output(task_id=2, name="Task 2")

        # Act
        self.helper.task_created(task1, "client-1")
        self.helper.task_updated(task2, ["priority"], "client-2")
        self.helper.task_deleted(3, "Task 3", "client-3")

        # Assert
        self.assertEqual(self.mock_background_tasks.add_task.call_count, 3)

        calls = self.mock_background_tasks.add_task.call_args_list
        self.assertEqual(
            calls[0], call(broadcast_task_created, self.mock_manager, task1, "client-1")
        )
        self.assertEqual(
            calls[1],
            call(
                broadcast_task_updated,
                self.mock_manager,
                task2,
                ["priority"],
                "client-2",
            ),
        )
        self.assertEqual(
            calls[2],
            call(broadcast_task_deleted, self.mock_manager, 3, "Task 3", "client-3"),
        )

    def test_helper_stores_manager_and_background_tasks(self):
        """Test that helper stores manager and background_tasks internally."""
        # Assert
        self.assertEqual(self.helper._manager, self.mock_manager)
        self.assertEqual(self.helper._background_tasks, self.mock_background_tasks)

    def test_add_background_task_schedules_task(self):
        """Test add_background_task schedules a generic background task."""

        # Arrange
        def sample_task(arg1: str, arg2: int) -> None:
            pass

        # Act
        self.helper.add_background_task(sample_task, "test", 123)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            sample_task, "test", 123
        )

    def test_add_background_task_with_kwargs(self):
        """Test add_background_task with keyword arguments."""

        # Arrange
        def sample_task(name: str, value: int) -> None:
            pass

        # Act
        self.helper.add_background_task(sample_task, name="test", value=456)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            sample_task, name="test", value=456
        )


if __name__ == "__main__":
    unittest.main()
