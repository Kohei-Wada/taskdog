"""Note editing utilities for TUI."""

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from textual.app import App

from domain.entities.task import Task
from domain.repositories.notes_repository import NotesRepository
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


def _create_temp_notes_file(task: Task, notes_repository: NotesRepository) -> Path:
    """Create temporary notes file with existing content or template.

    Args:
        task: Task whose notes to prepare
        notes_repository: Notes repository for reading existing content

    Returns:
        Path to the temporary notes file

    Raises:
        ValueError: If task.id is None
    """
    if task.id is None:
        raise ValueError("Task ID cannot be None")

    # Read existing notes or generate template
    existing_content = notes_repository.read_notes(task.id)
    content = existing_content if existing_content else generate_notes_template(task)

    # Create temporary file with .md suffix
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        return Path(tmp.name)


def _edit_and_save_notes(
    temp_path: Path,
    task: Task,
    notes_repository: NotesRepository,
    app: App[Any],
) -> None:
    """Open editor and save edited content.

    Args:
        temp_path: Path to temporary notes file
        task: Task being edited
        notes_repository: Notes repository for saving
        app: Textual app instance (for suspend)

    Raises:
        RuntimeError: If editor is not found
        subprocess.CalledProcessError: If editor exits with error
        KeyboardInterrupt: If editor is interrupted
        OSError: If file operations fail
        UnicodeDecodeError: If file encoding is invalid
        ValueError: If task.id is None
    """
    if task.id is None:
        raise ValueError("Task ID cannot be None")

    # Get editor
    editor = get_editor()

    # Open editor
    with app.suspend():
        subprocess.run([editor, str(temp_path)], check=True)

    # Read edited content
    edited_content = temp_path.read_text(encoding="utf-8")

    # Save via Domain interface
    notes_repository.write_notes(task.id, edited_content)


def _prepare_temp_file(
    task: Task,
    notes_repository: NotesRepository,
    on_error: Callable[[str, Exception], None] | None,
) -> Path | None:
    """Prepare temporary file, returning None on error.

    Args:
        task: Task to prepare notes for
        notes_repository: Notes repository
        on_error: Error callback

    Returns:
        Path to temp file, or None on error
    """
    try:
        return _create_temp_notes_file(task, notes_repository)
    except Exception as e:
        if on_error:
            on_error("preparing notes file", e)
        return None


def _execute_edit(
    temp_path: Path,
    task: Task,
    notes_repository: NotesRepository,
    app: App[Any],
    on_success: Callable[[str, int], None] | None,
    on_error: Callable[[str, Exception], None] | None,
) -> None:
    """Execute the edit operation with error handling.

    Args:
        temp_path: Path to temporary file
        task: Task being edited
        notes_repository: Notes repository
        app: Textual app instance
        on_success: Success callback
        on_error: Error callback
    """
    try:
        _edit_and_save_notes(temp_path, task, notes_repository, app)
        if on_success and task.id is not None:
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
    task: Task,
    notes_repository: NotesRepository,
    app: App[Any],
    on_success: Callable[[str, int], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
) -> None:
    """Open editor for the task's note using temporary file.

    This function uses a temporary file approach to avoid file-system implementation
    details, allowing it to work with any NotesRepository implementation.

    Args:
        task: Task whose note to edit
        notes_repository: Notes repository (Domain interface)
        app: Textual app instance (for suspend)
        on_success: Optional callback (task_name, task_id) on successful edit
        on_error: Optional callback (action, exception) on error
    """
    if task.id is None:
        if on_error:
            on_error("editing note", ValueError("Task ID is None"))
        return

    # Ensure notes directory exists
    notes_repository.ensure_notes_dir()

    # Prepare temporary file
    temp_path = _prepare_temp_file(task, notes_repository, on_error)
    if temp_path is None:
        return

    # Execute edit operation
    try:
        _execute_edit(temp_path, task, notes_repository, app, on_success, on_error)
    finally:
        # Always clean up temporary file
        temp_path.unlink(missing_ok=True)
