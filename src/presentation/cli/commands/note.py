"""Note command - Edit task notes in markdown."""

import os
import subprocess

import click

from presentation.cli.error_handler import handle_task_errors
from presentation.utils.notes_template import generate_notes_template
from utils.console_messages import print_error


def get_editor():
    """Get editor command from environment or fallback to defaults.

    Returns:
        str: Editor command (e.g., 'vim', 'nano', 'vi')

    Raises:
        RuntimeError: If no editor is found
    """
    # Try $EDITOR first
    editor = os.getenv("EDITOR")
    if editor:
        return editor

    # Fallback to common editors
    for fallback in ["vim", "nano", "vi"]:
        # Check if editor exists in PATH
        try:
            subprocess.run(
                ["which", fallback],
                check=True,
                capture_output=True,
                text=True,
            )
            return fallback
        except subprocess.CalledProcessError:
            continue

    # No editor found
    raise RuntimeError(
        "No editor found. Please set $EDITOR environment variable or install vim, nano, or vi."
    )


@click.command(name="note", help="Edit task notes in markdown ($EDITOR).")
@click.argument("task_id", type=int)
@click.pass_context
@handle_task_errors("editing notes")
def note_command(ctx, task_id):
    """Edit task notes in markdown."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]

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
        console.print(f"[green]✓[/green] Created notes file: {notes_path}")

    # Get editor
    try:
        editor = get_editor()
    except RuntimeError as e:
        print_error(console, "finding editor", e)
        return

    # Open editor
    console.print(f"[blue]Opening {editor}...[/blue]")
    try:
        subprocess.run([editor, str(notes_path)], check=True)
        console.print(f"[green]✓[/green] Notes saved for task #{task_id}")
    except subprocess.CalledProcessError as e:
        print_error(console, "running editor", e)
    except KeyboardInterrupt:
        console.print("\n[yellow]Editor interrupted[/yellow]")
