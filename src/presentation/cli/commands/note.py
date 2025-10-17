"""Note command - Edit task notes in markdown."""

import subprocess

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
    """Edit task notes in markdown."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    # Get task from repository
    task = repository.get_by_id(task_id)
    if not task:
        from domain.exceptions.task_exceptions import TaskNotFoundException

        raise TaskNotFoundException(task_id)

    # Get notes path
    notes_path = task.notes_path

    # Create notes directory if it doesn't exist
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate template if notes file doesn't exist
    if not notes_path.exists():
        template = generate_notes_template(task)
        notes_path.write_text(template, encoding="utf-8")
        console_writer.print(f"[green]✓[/green] Created notes file: {notes_path}")

    # Get editor
    try:
        editor = get_editor()
    except RuntimeError as e:
        console_writer.error("finding editor", e)
        return

    # Open editor
    console_writer.print(f"[blue]Opening {editor}...[/blue]")
    try:
        subprocess.run([editor, str(notes_path)], check=True)
        console_writer.print(f"[green]✓[/green] Notes saved for task #{task_id}")
    except subprocess.CalledProcessError as e:
        console_writer.error("running editor", e)
    except KeyboardInterrupt:
        print("\n")  # Add newline after ^C
        console_writer.warning("Editor interrupted")
