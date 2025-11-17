from typing import Any

import click
from rich.console import Console

from taskdog.cli.commands.add import add_command
from taskdog.cli.commands.add_dependency import add_dependency_command
from taskdog.cli.commands.cancel import cancel_command
from taskdog.cli.commands.deadline import deadline_command
from taskdog.cli.commands.done import done_command
from taskdog.cli.commands.estimate import estimate_command
from taskdog.cli.commands.export import export_command
from taskdog.cli.commands.gantt import gantt_command
from taskdog.cli.commands.log_hours import log_hours_command
from taskdog.cli.commands.note import note_command
from taskdog.cli.commands.optimize import optimize_command
from taskdog.cli.commands.pause import pause_command
from taskdog.cli.commands.priority import priority_command
from taskdog.cli.commands.remove_dependency import remove_dependency_command
from taskdog.cli.commands.rename import rename_command
from taskdog.cli.commands.reopen import reopen_command
from taskdog.cli.commands.report import report_command
from taskdog.cli.commands.restore import restore_command
from taskdog.cli.commands.rm import rm_command
from taskdog.cli.commands.schedule import schedule_command
from taskdog.cli.commands.show import show_command
from taskdog.cli.commands.start import start_command
from taskdog.cli.commands.stats import stats_command
from taskdog.cli.commands.table import table_command
from taskdog.cli.commands.tags import tags_command
from taskdog.cli.commands.today import today_command
from taskdog.cli.commands.tui_command import tui_command
from taskdog.cli.commands.update import update_command
from taskdog.cli.commands.week import week_command
from taskdog.cli.context import CliContext
from taskdog.console.rich_console_writer import RichConsoleWriter
from taskdog_core.shared.config_manager import ConfigManager


class TaskdogGroup(click.Group):
    """Custom Click Group that displays ASCII art before help."""

    def format_help(self, ctx: click.Context, formatter: Any) -> None:
        """Override format_help to add ASCII art before help text."""
        from taskdog.constants.ascii_art import (
            TASKDOG_ASCII_ART,
            TASKDOG_DESCRIPTION,
            TASKDOG_TAGLINE,
        )

        console = Console()
        console.print(TASKDOG_ASCII_ART, style="cyan")
        console.print(f"  {TASKDOG_TAGLINE}", style="bold yellow")
        console.print(f"  {TASKDOG_DESCRIPTION}", style="dim")
        console.print()

        # Call the original format_help
        super().format_help(ctx, formatter)


@click.group(
    cls=TaskdogGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Taskdog: Task management CLI tool with time tracking and optimization."""
    # Display help when no subcommand is provided
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    # Initialize shared dependencies
    console = Console()
    console_writer = RichConsoleWriter(console)
    config = ConfigManager.load()

    # API client is now required for all CLI commands
    # Check if API mode is enabled in config
    if not config.api.enabled:
        console_writer.error(
            "initializing CLI",
            Exception(
                "API mode is required. Please enable it in config file or set TASKDOG_API_URL environment variable."
            ),
        )
        ctx.exit(1)

    # Initialize API client (required)
    from taskdog.infrastructure.api_client import TaskdogApiClient

    try:
        api_client = TaskdogApiClient(
            base_url=f"http://{config.api.host}:{config.api.port}"
        )
        # Test connection
        api_client.client.get("/health")
    except Exception as e:
        console_writer.error(
            "connecting to API server",
            Exception(
                f"Cannot connect to API server at {config.api.host}:{config.api.port}. "
                f"Please start the server first with 'taskdog-server'. Error: {e}"
            ),
        )
        ctx.exit(1)

    # Store in CliContext for type-safe access
    ctx.ensure_object(dict)
    ctx.obj = CliContext(
        console_writer=console_writer,
        api_client=api_client,
        config=config,
    )


cli.add_command(add_command)
cli.add_command(add_dependency_command)
cli.add_command(table_command)
cli.add_command(export_command)
cli.add_command(rm_command)
cli.add_command(update_command)
cli.add_command(start_command)
cli.add_command(pause_command)
cli.add_command(done_command)
cli.add_command(cancel_command)
cli.add_command(gantt_command)
cli.add_command(log_hours_command)
cli.add_command(today_command)
cli.add_command(week_command)
cli.add_command(note_command)
cli.add_command(show_command)
cli.add_command(deadline_command)
cli.add_command(priority_command)
cli.add_command(remove_dependency_command)
cli.add_command(rename_command)
cli.add_command(reopen_command)
cli.add_command(report_command)
cli.add_command(restore_command)
cli.add_command(estimate_command)
cli.add_command(schedule_command)
cli.add_command(optimize_command)
cli.add_command(stats_command)
cli.add_command(tags_command)
cli.add_command(tui_command)

if __name__ == "__main__":
    cli()
