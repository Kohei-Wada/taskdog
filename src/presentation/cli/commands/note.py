"""Note command - Edit task notes in markdown."""

import subprocess
import tempfile
from pathlib import Path

import click

from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from presentation.utils.editor import get_editor
from presentation.utils.notes_template import generate_notes_template


@click.command(name="note", help="Edit task notes in markdown ($EDITOR).")
@click.argument("task_id", type=int)
@click.pass_context
@handle_task_errors("editing notes")
def note_command(ctx, task_id):
    """Edit task notes in markdown using temporary file approach."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    notes_repository = ctx_obj.notes_repository

    # Get task from repository
    task = repository.get_by_id(task_id)
    if not task:
        from domain.exceptions.task_exceptions import TaskNotFoundException

        raise TaskNotFoundException(task_id)

    # Ensure notes directory exists
    notes_repository.ensure_notes_dir()

    # Read existing notes or generate template
    existing_content = notes_repository.read_notes(task_id)
    content = existing_content if existing_content else generate_notes_template(task)

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        temp_path = Path(tmp.name)

    try:
        # Get editor
        try:
            editor = get_editor()
        except RuntimeError as e:
            console_writer.error("finding editor", e)
            return

        # Open editor
        console_writer.info(f"Opening {editor}...")
        try:
            subprocess.run([editor, str(temp_path)], check=True)

            # Read edited content
            edited_content = temp_path.read_text(encoding="utf-8")

            # Save via Domain interface
            notes_repository.write_notes(task_id, edited_content)

            console_writer.success(f"Notes saved for task #{task_id}")

        except subprocess.CalledProcessError as e:
            console_writer.error("running editor", e)
        except KeyboardInterrupt:
            print("\n")  # Add newline after ^C
            console_writer.warning("Editor interrupted")
        except (OSError, UnicodeDecodeError) as e:
            console_writer.error("saving notes", e)

    finally:
        # Always clean up temporary file
        temp_path.unlink(missing_ok=True)
