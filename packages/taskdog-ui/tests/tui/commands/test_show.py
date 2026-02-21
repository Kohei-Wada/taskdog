"""Tests for ShowCommand."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from taskdog.tui.commands.show import ShowCommand
from taskdog_core.application.dto.task_detail_output import TaskDetailOutput
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
        actual_duration=None,
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


class TestShowCommand:
    """Test cases for ShowCommand."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ShowCommand(self.mock_app, self.mock_context)

    def test_execute_impl_warns_when_no_task_selected(self) -> None:
        """Test warning when no task is selected."""
        self.command.get_selected_task_id = MagicMock(return_value=None)
        self.command.notify_warning = MagicMock()

        self.command.execute_impl()

        self.command.notify_warning.assert_called_once()
        assert "no task selected" in self.command.notify_warning.call_args[0][0].lower()

    def test_execute_impl_runs_worker(self) -> None:
        """Test that a worker is started for async fetch."""
        self.command.get_selected_task_id = MagicMock(return_value=42)

        self.command.execute_impl()

        self.mock_app.run_worker.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_show_detail_fetches_task_detail(self) -> None:
        """Test that task detail is fetched from API in background thread."""
        task = create_mock_task_dto(task_id=42)
        detail = TaskDetailOutput(task=task, notes_content="", has_notes=False)
        self.mock_context.api_client.get_task_detail.return_value = detail

        await self.command._fetch_and_show_detail(42)

        self.mock_context.api_client.get_task_detail.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_fetch_and_show_detail_pushes_detail_dialog(self) -> None:
        """Test that detail dialog is pushed after fetch."""
        task = create_mock_task_dto(task_id=42)
        detail = TaskDetailOutput(task=task, notes_content="", has_notes=False)
        self.mock_context.api_client.get_task_detail.return_value = detail

        await self.command._fetch_and_show_detail(42)

        self.mock_app.push_screen.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_show_detail_notifies_error_on_failure(self) -> None:
        """Test that API errors are caught and shown as notifications."""
        self.mock_context.api_client.get_task_detail.side_effect = ConnectionError(
            "Connection refused"
        )
        self.command.notify_error = MagicMock()

        await self.command._fetch_and_show_detail(42)

        self.command.notify_error.assert_called_once()
        self.mock_app.push_screen.assert_not_called()


class TestShowCommandHandleDetailScreenResult:
    """Test cases for ShowCommand._handle_detail_screen_result."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ShowCommand(self.mock_app, self.mock_context)

    def test_handle_none_result_does_nothing(self) -> None:
        """Test that None result is ignored."""
        self.command._edit_note = MagicMock()

        self.command._handle_detail_screen_result(None)

        self.command._edit_note.assert_not_called()

    def test_handle_note_action_triggers_edit(self) -> None:
        """Test that 'note' action triggers note editing."""
        self.command._edit_note = MagicMock()

        self.command._handle_detail_screen_result(("note", 42))

        self.command._edit_note.assert_called_once_with(42)

    def test_handle_invalid_result_format_ignored(self) -> None:
        """Test that invalid result format is ignored."""
        self.command._edit_note = MagicMock()

        # Single value instead of tuple
        self.command._handle_detail_screen_result("invalid")

        self.command._edit_note.assert_not_called()

    def test_handle_unknown_action_ignored(self) -> None:
        """Test that unknown actions are ignored."""
        self.command._edit_note = MagicMock()

        self.command._handle_detail_screen_result(("unknown", 42))

        self.command._edit_note.assert_not_called()


class TestShowCommandEditNote:
    """Test cases for ShowCommand._edit_note."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ShowCommand(self.mock_app, self.mock_context)

    def test_edit_note_delegates_to_note_command(self) -> None:
        """Test that _edit_note delegates to NoteCommand with correct args."""
        from unittest.mock import patch

        with patch(
            "taskdog.tui.commands.note.NoteCommand", wraps=None
        ) as mock_note_cmd_cls:
            mock_cmd_instance = MagicMock()
            mock_note_cmd_cls.return_value = mock_cmd_instance

            self.command._edit_note(42)

            mock_note_cmd_cls.assert_called_once()
            call_kwargs = mock_note_cmd_cls.call_args
            assert call_kwargs[0][0] is self.mock_app
            assert call_kwargs[0][1] is self.mock_context
            assert call_kwargs[1]["task_id"] == 42
            assert call_kwargs[1]["on_success"] is not None
            mock_cmd_instance.execute.assert_called_once()


class TestShowCommandOnEditSuccess:
    """Test cases for ShowCommand._on_edit_success."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_context = MagicMock()
        self.command = ShowCommand(self.mock_app, self.mock_context)

    def test_does_not_show_explicit_notification(self) -> None:
        """Test that no explicit notification is shown (handled via WebSocket)."""
        self.command.notify_success = MagicMock()
        self.command.execute = MagicMock()

        self.command._on_edit_success("Test Task", 42)

        # Notification is handled via WebSocket (task_updated event),
        # not via explicit notify_success call
        self.command.notify_success.assert_not_called()

    def test_re_displays_detail_screen(self) -> None:
        """Test that execute is called to re-display screen."""
        self.command.execute = MagicMock()

        self.command._on_edit_success("Task", 1)

        self.command.execute.assert_called_once()
