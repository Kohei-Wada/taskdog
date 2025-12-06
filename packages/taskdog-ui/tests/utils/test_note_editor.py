"""Tests for note_editor utility."""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from taskdog.utils.note_editor import (
    _create_temp_notes_file,
    _execute_edit,
    _prepare_temp_file,
    edit_task_note,
)
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.domain.entities.task import TaskStatus


def create_mock_task(
    task_id: int = 1,
    name: str = "Test Task",
) -> TaskDetailDto:
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
        actual_daily_hours={},
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


class TestCreateTempNotesFile:
    """Test cases for _create_temp_notes_file function."""

    def test_creates_temp_file_with_existing_content(self) -> None:
        """Test creating temp file with existing notes content."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.return_value = ("Existing notes", True)

        result = _create_temp_notes_file(task, notes_provider)

        assert result.exists()
        assert result.suffix == ".md"
        content = result.read_text(encoding="utf-8")
        assert content == "Existing notes"
        result.unlink()  # Cleanup

    @patch("taskdog.utils.note_editor.get_note_template")
    def test_creates_temp_file_with_template_when_no_content(
        self, mock_template: MagicMock
    ) -> None:
        """Test creating temp file with template when no existing content."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.return_value = ("", False)
        mock_template.return_value = "# Template content"

        result = _create_temp_notes_file(task, notes_provider)

        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert content == "# Template content"
        result.unlink()  # Cleanup

    def test_file_has_md_suffix(self) -> None:
        """Test that created file has .md suffix."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.return_value = ("content", True)

        result = _create_temp_notes_file(task, notes_provider)

        assert result.suffix == ".md"
        result.unlink()  # Cleanup


class TestPrepareTempFile:
    """Test cases for _prepare_temp_file function."""

    def test_returns_path_on_success(self) -> None:
        """Test successful temp file preparation."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.return_value = ("content", True)
        on_error = MagicMock()

        result = _prepare_temp_file(task, notes_provider, on_error)

        assert result is not None
        assert result.exists()
        on_error.assert_not_called()
        result.unlink()  # Cleanup

    def test_returns_none_and_calls_error_callback_on_exception(self) -> None:
        """Test error handling during temp file preparation."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.side_effect = Exception("API Error")
        on_error = MagicMock()

        result = _prepare_temp_file(task, notes_provider, on_error)

        assert result is None
        on_error.assert_called_once()
        call_args = on_error.call_args
        assert "preparing notes file" in call_args[0][0]

    def test_returns_none_without_callback_on_exception(self) -> None:
        """Test error handling without callback."""
        task = create_mock_task()
        notes_provider = MagicMock()
        notes_provider.get_task_notes.side_effect = Exception("API Error")

        result = _prepare_temp_file(task, notes_provider, None)

        assert result is None


class TestExecuteEdit:
    """Test cases for _execute_edit function."""

    @patch("taskdog.utils.note_editor._edit_and_save_notes")
    def test_calls_success_callback_on_success(self, mock_edit_save: MagicMock) -> None:
        """Test success callback is called."""
        task = create_mock_task(task_id=42, name="Test Task")
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()
        temp_path = Path("/tmp/test.md")

        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)

        on_success.assert_called_once_with("Test Task", 42)
        on_error.assert_not_called()

    @patch("taskdog.utils.note_editor._edit_and_save_notes")
    def test_calls_error_callback_on_runtime_error(
        self, mock_edit_save: MagicMock
    ) -> None:
        """Test error callback on RuntimeError."""
        mock_edit_save.side_effect = RuntimeError("No editor found")
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()
        temp_path = Path("/tmp/test.md")

        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)

        on_error.assert_called_once()
        assert "finding editor" in on_error.call_args[0][0]
        on_success.assert_not_called()

    @patch("taskdog.utils.note_editor._edit_and_save_notes")
    def test_calls_error_callback_on_called_process_error(
        self, mock_edit_save: MagicMock
    ) -> None:
        """Test error callback on subprocess.CalledProcessError."""
        mock_edit_save.side_effect = subprocess.CalledProcessError(1, "vim")
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()
        temp_path = Path("/tmp/test.md")

        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)

        on_error.assert_called_once()
        assert "running editor" in on_error.call_args[0][0]

    @patch("taskdog.utils.note_editor._edit_and_save_notes")
    def test_calls_error_callback_on_keyboard_interrupt(
        self, mock_edit_save: MagicMock
    ) -> None:
        """Test error callback on KeyboardInterrupt."""
        mock_edit_save.side_effect = KeyboardInterrupt()
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()
        temp_path = Path("/tmp/test.md")

        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)

        on_error.assert_called_once()
        assert "editor" in on_error.call_args[0][0]

    @patch("taskdog.utils.note_editor._edit_and_save_notes")
    def test_calls_error_callback_on_oserror(self, mock_edit_save: MagicMock) -> None:
        """Test error callback on OSError."""
        mock_edit_save.side_effect = OSError("Permission denied")
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()
        temp_path = Path("/tmp/test.md")

        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)

        on_error.assert_called_once()
        assert "saving notes" in on_error.call_args[0][0]


class TestEditTaskNote:
    """Test cases for edit_task_note function."""

    @patch("taskdog.utils.note_editor._execute_edit")
    @patch("taskdog.utils.note_editor._prepare_temp_file")
    def test_returns_early_when_temp_file_preparation_fails(
        self, mock_prepare: MagicMock, mock_execute: MagicMock
    ) -> None:
        """Test early return when temp file preparation fails."""
        mock_prepare.return_value = None
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()

        edit_task_note(task, notes_provider, app)

        mock_execute.assert_not_called()

    @patch("taskdog.utils.note_editor._execute_edit")
    @patch("taskdog.utils.note_editor._prepare_temp_file")
    def test_cleans_up_temp_file_after_success(
        self, mock_prepare: MagicMock, mock_execute: MagicMock
    ) -> None:
        """Test temp file is cleaned up after successful edit."""
        temp_path = MagicMock(spec=Path)
        mock_prepare.return_value = temp_path
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()

        edit_task_note(task, notes_provider, app)

        temp_path.unlink.assert_called_once_with(missing_ok=True)

    @patch("taskdog.utils.note_editor._execute_edit")
    @patch("taskdog.utils.note_editor._prepare_temp_file")
    def test_cleans_up_temp_file_on_exception(
        self, mock_prepare: MagicMock, mock_execute: MagicMock
    ) -> None:
        """Test temp file is cleaned up even on exception."""
        temp_path = MagicMock(spec=Path)
        mock_prepare.return_value = temp_path
        mock_execute.side_effect = RuntimeError("Unexpected error")
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()

        with pytest.raises(RuntimeError):
            edit_task_note(task, notes_provider, app)

        temp_path.unlink.assert_called_once_with(missing_ok=True)

    @patch("taskdog.utils.note_editor._execute_edit")
    @patch("taskdog.utils.note_editor._prepare_temp_file")
    def test_passes_callbacks_to_execute(
        self, mock_prepare: MagicMock, mock_execute: MagicMock
    ) -> None:
        """Test callbacks are passed to _execute_edit."""
        temp_path = MagicMock(spec=Path)
        mock_prepare.return_value = temp_path
        task = create_mock_task()
        notes_provider = MagicMock()
        app = MagicMock()
        on_success = MagicMock()
        on_error = MagicMock()

        edit_task_note(
            task, notes_provider, app, on_success=on_success, on_error=on_error
        )

        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0][4] == on_success
        assert call_args[0][5] == on_error
