"""Note editing utilities for TUI."""

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from textual.app import App

from taskdog.infrastructure.cli_config_manager import CliConfig
from taskdog.utils.editor import get_editor
from taskdog.utils.notes_template import get_note_template
from taskdog_core.application.dto.task_dto import TaskDetailDto


class NotesProvider(Protocol):
    """Protocol for notes access (supports both API client and NotesRepository)."""

    def get_task_notes(self, task_id: int) -> tuple[str, bool]:
        """Get task notes.

        Args:
            task_id: Task ID

        Returns:
            Tuple of (content, has_notes)
        """
        ...

    def update_task_notes(self, task_id: int, content: str) -> None:
        """Update task notes.

        Args:
            task_id: Task ID
            content: Notes content
        """
        ...


def _create_temp_notes_file(
    task: TaskDetailDto,
    notes_provider: NotesProvider,
    config: CliConfig | None = None,
) -> Path:
    """Create temporary notes file with existing content or template.

    Args:
        task: Task DTO whose notes to prepare
        notes_provider: Notes provider for reading existing content
        config: CLI configuration for custom template (optional)

    Returns:
        Path to the temporary notes file
    """
    # task.id is guaranteed to be int in TaskDetailDto (not Optional)
    existing_content, _ = notes_provider.get_task_notes(task.id)
    content = existing_content if existing_content else get_note_template(task, config)

    # Create temporary file with .md suffix
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
        return Path(tmp.name)


def _edit_and_save_notes(
    temp_path: Path,
    task: TaskDetailDto,
    notes_provider: NotesProvider,
    app: App[Any],
) -> bool:
    """Open editor and save edited content.

    Args:
        temp_path: Path to temporary notes file
        task: Task DTO being edited
        notes_provider: Notes provider for saving
        app: Textual app instance (for suspend)

    Returns:
        True if notes were changed and saved, False if no changes

    Raises:
        RuntimeError: If editor is not found
        subprocess.CalledProcessError: If editor exits with error
        KeyboardInterrupt: If editor is interrupted
        OSError: If file operations fail
        UnicodeDecodeError: If file encoding is invalid
    """
    # task.id is guaranteed to be int in TaskDetailDto (not Optional)

    # Get editor
    editor = get_editor()

    # Read original content before editing
    original_content = temp_path.read_text(encoding="utf-8")

    # Open editor
    with app.suspend():
        subprocess.run([editor, str(temp_path)], check=True)

    # Read edited content
    edited_content = temp_path.read_text(encoding="utf-8")

    # Check if content changed (normalize trailing whitespace for comparison,
    # as editors like vim may add trailing newline)
    if edited_content.rstrip() == original_content.rstrip():
        return False

    # Save via NotesProvider interface
    notes_provider.update_task_notes(task.id, edited_content)
    return True


def _prepare_temp_file(
    task: TaskDetailDto,
    notes_provider: NotesProvider,
    on_error: Callable[[str, Exception], None] | None,
    config: CliConfig | None = None,
) -> Path | None:
    """Prepare temporary file, returning None on error.

    Args:
        task: Task DTO to prepare notes for
        notes_provider: Notes provider
        on_error: Error callback
        config: CLI configuration for custom template (optional)

    Returns:
        Path to temp file, or None on error
    """
    try:
        return _create_temp_notes_file(task, notes_provider, config)
    except Exception as e:
        if on_error:
            on_error("preparing notes file", e)
        return None


def _execute_edit(
    temp_path: Path,
    task: TaskDetailDto,
    notes_provider: NotesProvider,
    app: App[Any],
    on_success: Callable[[str, int], None] | None,
    on_error: Callable[[str, Exception], None] | None,
) -> None:
    """Execute the edit operation with error handling.

    Args:
        temp_path: Path to temporary file
        task: Task DTO being edited
        notes_provider: Notes provider
        app: Textual app instance
        on_success: Success callback (called only if notes were changed)
        on_error: Error callback
    """
    try:
        changed = _edit_and_save_notes(temp_path, task, notes_provider, app)
        if changed and on_success:
            on_success(task.name, task.id)
    except RuntimeError as e:
        if on_error:
            on_error("finding editor", e)
    except subprocess.CalledProcessError as e:
        if on_error:
            on_error("running editor", e)
    except KeyboardInterrupt:
        if on_error:
            on_error("editor", RuntimeError("Editor interrupted"))
    except (OSError, UnicodeDecodeError) as e:
        if on_error:
            on_error("saving notes", e)


def edit_task_note(
    task: TaskDetailDto,
    notes_provider: NotesProvider,
    app: App[Any],
    on_success: Callable[[str, int], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
    config: CliConfig | None = None,
) -> None:
    """Open editor for the task's note using temporary file.

    This function uses a temporary file approach to work with any NotesProvider
    implementation (API client or NotesRepository).

    Args:
        task: Task DTO whose note to edit
        notes_provider: Notes provider (API client or NotesRepository)
        app: Textual app instance (for suspend)
        on_success: Optional callback (task_name, task_id) on successful edit
        on_error: Optional callback (action, exception) on error
        config: CLI configuration for custom template (optional)
    """
    # task.id is guaranteed to be int in TaskDetailDto (not Optional)

    # Prepare temporary file
    temp_path = _prepare_temp_file(task, notes_provider, on_error, config)
    if temp_path is None:
        return

    # Execute edit operation
    try:
        _execute_edit(temp_path, task, notes_provider, app, on_success, on_error)
    finally:
        # Always clean up temporary file
        temp_path.unlink(missing_ok=True)
