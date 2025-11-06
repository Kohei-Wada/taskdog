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

    TUI now requires an API client connection (same as all other CLI commands).
    """
    ctx_obj: CliContext = ctx.obj
    api_client = ctx_obj.api_client
    config = ctx_obj.config
    notes_repository = ctx_obj.notes_repository
    holiday_checker = ctx_obj.holiday_checker

    # Launch the TUI application with API client
    app = TaskdogTUI(
        api_client=api_client,
        notes_repository=notes_repository,
        config=config,
        holiday_checker=holiday_checker,
    )
    app.run()
