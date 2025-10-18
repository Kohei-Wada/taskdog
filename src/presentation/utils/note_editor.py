"""Note editing utilities for TUI."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from textual.app import App

from domain.entities.task import Task
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


def _prepare_notes_file(task: Task) -> Path:
    """Prepare notes file for editing.

    Args:
        task: Task whose notes to prepare

    Returns:
        Path to the notes file
    """
    notes_path = task.notes_path
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    if not notes_path.exists():
        template = generate_notes_template(task)
        notes_path.write_text(template, encoding="utf-8")

    return notes_path


def _open_editor(
    notes_path: Path,
    editor: str,
    app: App,
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
    app: App,
    on_success: Callable[[str, int], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
) -> None:
    """Open editor for the task's note.

    Args:
        task: Task whose note to edit
        app: Textual app instance (for suspend)
        on_success: Optional callback (task_name, task_id) on successful edit
        on_error: Optional callback (action, exception) on error
    """
    if task.id is None:
        if on_error:
            on_error("editing note", ValueError("Task ID is None"))
        return

    # Prepare notes file
    notes_path = _prepare_notes_file(task)

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
