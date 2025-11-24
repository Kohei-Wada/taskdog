"""TUI command - Launch the Text User Interface."""

import click

from taskdog.cli.context import CliContext
from taskdog.tui.app import TaskdogTUI


@click.command(
    name="tui", help="Launch the Text User Interface for interactive task management."
)
@click.pass_context
def tui_command(ctx: click.Context) -> None:
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
    cli_config = ctx_obj.config

    # Launch the TUI application with API client and config
    app = TaskdogTUI(api_client=api_client, cli_config=cli_config)
    app.run()
