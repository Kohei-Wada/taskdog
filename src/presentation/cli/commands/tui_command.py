"""TUI command - Launch the Text User Interface."""

import click

from presentation.cli.context import CliContext
from presentation.tui.app import TaskdogTUI


@click.command(name="tui", help="Launch the Text User Interface for interactive task management.")
@click.pass_context
def tui_command(ctx):
    """Launch the TUI for interactive task management.

    The TUI provides a full-screen interface with keyboard shortcuts:
    - ↑/↓: Navigate tasks
    - s: Start selected task
    - d: Complete selected task
    - a: Add new task
    - Delete: Remove selected task
    - Enter: Show task details
    - r: Refresh task list
    - q: Quit
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    config = ctx_obj.config
    notes_repository = ctx_obj.notes_repository

    # Launch the TUI application
    app = TaskdogTUI(
        repository=repository,
        time_tracker=time_tracker,
        notes_repository=notes_repository,
        config=config,
    )
    app.run()
