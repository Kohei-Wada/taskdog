"""Tests for AddCommand."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.add import AddCommand
from taskdog.tui.forms.task_form_fields import TaskFormData
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task_dto(task_id: int = 1, name: str = "Test Task") -> TaskDetailDto:
    """Create a mock TaskDetailDto for testing."""
    return TaskDetailDto(
        id=task_id,
        name=name,
        priority=50,
        status=TaskStatus.PENDING,
        planned_start=None,
        planned_end=None,
        deadline=None,
        actual_start=None,
        actual_end=None,
        estimated_duration=None,
        daily_allocations={},
        is_fixed=False,
        depends_on=[],
        tags=[],
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        actual_duration_hours=None,
        is_active=False,
        is_finished=False,
        can_be_modified=True,
        is_schedulable=True,
    )


class TestAddCommand:
    """Test cases for AddCommand."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = AddCommand(self.mock_app, self.mock_context)

    def test_execute_pushes_dialog(self) -> None:
        """Test that execute pushes TaskFormDialog."""
        self.command.execute()

        self.mock_app.push_screen.assert_called_once()
        # First argument is the dialog instance
        call_args = self.mock_app.push_screen.call_args
        dialog = call_args[0][0]
        # Verify it's in add mode (no task)
        assert dialog.task_to_edit is None
        assert dialog.is_edit_mode is False

    def test_execute_provides_callback(self) -> None:
        """Test that execute provides a callback for dialog result."""
        self.command.execute()

        call_args = self.mock_app.push_screen.call_args
        # Second argument should be the callback
        callback = call_args[0][1]
        assert callable(callback)


class TestAddCommandHandleTaskData:
    """Test cases for AddCommand's task data handling."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = AddCommand(self.mock_app, self.mock_context)

    def test_handle_cancelled_dialog(self) -> None:
        """Test handling when user cancels dialog."""
        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        # Simulate cancelled dialog (returns None)
        callback(None)

        # API client should not be called
        self.mock_context.api_client.create_task.assert_not_called()

    def test_handle_form_data_creates_task(self) -> None:
        """Test handling form data creates task via API."""
        created_task = create_mock_task_dto(task_id=42, name="New Task")
        self.mock_context.api_client.create_task.return_value = created_task

        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        form_data = TaskFormData(
            name="New Task",
            priority=75,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            is_fixed=False,
            depends_on=[],
            tags=[],
        )

        callback(form_data)

        self.mock_context.api_client.create_task.assert_called_once()
        call_kwargs = self.mock_context.api_client.create_task.call_args[1]
        assert call_kwargs["name"] == "New Task"
        assert call_kwargs["priority"] == 75

    def test_handle_form_data_posts_task_created_event(self) -> None:
        """Test that TaskCreated event is posted after creation."""
        created_task = create_mock_task_dto(task_id=99)
        self.mock_context.api_client.create_task.return_value = created_task

        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        form_data = TaskFormData(name="Task", priority=50)
        callback(form_data)

        self.mock_app.post_message.assert_called_once()
        message = self.mock_app.post_message.call_args[0][0]
        assert message.task_id == 99

    def test_handle_form_data_with_dependencies(self) -> None:
        """Test handling form data with dependencies."""
        created_task = create_mock_task_dto(task_id=10)
        self.mock_context.api_client.create_task.return_value = created_task
        self.command.manage_dependencies = MagicMock(return_value=[])

        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        form_data = TaskFormData(
            name="Task with deps",
            priority=50,
            depends_on=[1, 2, 3],
        )

        callback(form_data)

        self.command.manage_dependencies.assert_called_once()
        call_kwargs = self.command.manage_dependencies.call_args[1]
        assert set(call_kwargs["add_deps"]) == {1, 2, 3}

    def test_handle_form_data_warns_on_dependency_failure(self) -> None:
        """Test warning is shown when dependencies fail."""
        created_task = create_mock_task_dto(task_id=10)
        self.mock_context.api_client.create_task.return_value = created_task
        self.command.manage_dependencies = MagicMock(
            return_value=["Failed to add #999"]
        )
        self.command.notify_warning = MagicMock()

        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        form_data = TaskFormData(
            name="Task with deps",
            priority=50,
            depends_on=[999],
        )

        callback(form_data)

        self.command.notify_warning.assert_called_once()
        warning_msg = self.command.notify_warning.call_args[0][0]
        assert "dependencies failed" in warning_msg.lower()

    def test_handle_form_data_with_tags(self) -> None:
        """Test handling form data with tags."""
        created_task = create_mock_task_dto(task_id=10)
        self.mock_context.api_client.create_task.return_value = created_task

        self.command.execute()
        callback = self.mock_app.push_screen.call_args[0][1]

        form_data = TaskFormData(
            name="Task with tags",
            priority=50,
            tags=["urgent", "work"],
        )

        callback(form_data)

        call_kwargs = self.mock_context.api_client.create_task.call_args[1]
        assert call_kwargs["tags"] == ["urgent", "work"]
