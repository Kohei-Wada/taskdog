"""Note editing utilities for TUI."""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from textual.app import App

from domain.entities.task import Task
from infrastructure.persistence.file_notes_repository import FileNotesRepository
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


def _prepare_notes_file(task: Task, notes_repository: FileNotesRepository) -> Path:
    """Prepare notes file for editing.

    Args:
        task: Task whose notes to prepare
        notes_repository: Notes repository for file operations

    Returns:
        Path to the notes file

    Raises:
        ValueError: If task.id is None
    """
    if task.id is None:
        raise ValueError("Task ID cannot be None")

    notes_path = notes_repository.get_notes_path(task.id)
    notes_repository.ensure_notes_dir()

    if not notes_path.exists():
        template = generate_notes_template(task)
        notes_repository.write_notes(task.id, template)

    return notes_path


def _open_editor(
    notes_path: Path,
    editor: str,
    app: App[Any],
) -> None:
    """Open editor for notes file.

    Args:
        notes_path: Path to the notes file
        editor: Editor command
        app: Textual app instance (for suspend)

    Raises:
        subprocess.CalledProcessError: If editor exits with error
        KeyboardInterrupt: If editor is interrupted
    """
    with app.suspend():
        subprocess.run([editor, str(notes_path)], check=True)


def edit_task_note(
    task: Task,
    notes_repository: FileNotesRepository,
    app: App[Any],
    on_success: Callable[[str, int], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
) -> None:
    """Open editor for the task's note.

    Args:
        task: Task whose note to edit
        notes_repository: Notes repository for file operations
        app: Textual app instance (for suspend)
        on_success: Optional callback (task_name, task_id) on successful edit
        on_error: Optional callback (action, exception) on error
    """
    if task.id is None:
        if on_error:
            on_error("editing note", ValueError("Task ID is None"))
        return

    # Prepare notes file
    notes_path = _prepare_notes_file(task, notes_repository)

    # Get editor
    try:
        editor = get_editor()
    except RuntimeError as e:
        if on_error:
            on_error("finding editor", e)
        return

    # Open editor
    try:
        _open_editor(notes_path, editor, app)
        if on_success:
            on_success(task.name, task.id)
    except subprocess.CalledProcessError as e:
        if on_error:
            on_error("running editor", e)
    except KeyboardInterrupt:
        if on_error:
            on_error("editor", RuntimeError("Editor interrupted"))
