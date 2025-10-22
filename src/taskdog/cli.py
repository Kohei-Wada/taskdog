import click
from rich.console import Console

from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.cli.commands.add import add_command
from presentation.cli.commands.add_dependency import add_dependency_command
from presentation.cli.commands.cancel import cancel_command
from presentation.cli.commands.deadline import deadline_command
from presentation.cli.commands.done import done_command
from presentation.cli.commands.estimate import estimate_command
from presentation.cli.commands.export import export_command
from presentation.cli.commands.gantt import gantt_command
from presentation.cli.commands.log_hours import log_hours_command
from presentation.cli.commands.note import note_command
from presentation.cli.commands.optimize import optimize_command
from presentation.cli.commands.pause import pause_command
from presentation.cli.commands.priority import priority_command
from presentation.cli.commands.remove_dependency import remove_dependency_command
from presentation.cli.commands.rename import rename_command
from presentation.cli.commands.reopen import reopen_command
from presentation.cli.commands.restore import restore_command
from presentation.cli.commands.rm import rm_command
from presentation.cli.commands.schedule import schedule_command
from presentation.cli.commands.show import show_command
from presentation.cli.commands.start import start_command
from presentation.cli.commands.stats import stats_command
from presentation.cli.commands.table import table_command
from presentation.cli.commands.today import today_command
from presentation.cli.commands.tui_command import tui_command
from presentation.cli.commands.update import update_command
from presentation.cli.context import CliContext
from presentation.console.rich_console_writer import RichConsoleWriter
from shared.config_manager import ConfigManager
from shared.xdg_utils import XDGDirectories


class TaskdogGroup(click.Group):
    """Custom Click Group that displays ASCII art before help."""

    def format_help(self, ctx, formatter):
        """Override format_help to add ASCII art before help text."""
        from presentation.constants.ascii_art import (
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
def cli(ctx):
    """Taskdog: Task management CLI tool with time tracking and optimization."""
    from domain.exceptions.task_exceptions import CorruptedDataError

    # Display help when no subcommand is provided
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    # Follow XDG Base Directory specification
    tasksfile = str(XDGDirectories.get_tasks_file())

    # Initialize shared dependencies
    console = Console()
    console_writer = RichConsoleWriter(console)
    time_tracker = TimeTracker()
    config = ConfigManager.load()

    # Initialize repository with error handling for corrupted data
    try:
        repository = JsonTaskRepository(tasksfile)
    except CorruptedDataError as e:
        # Display detailed error message
        console_writer.error("loading tasks", e)
        ctx.exit(1)

    # Store in CliContext for type-safe access
    ctx.ensure_object(dict)
    ctx.obj = CliContext(
        console_writer=console_writer,
        repository=repository,
        time_tracker=time_tracker,
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
cli.add_command(note_command)
cli.add_command(show_command)
cli.add_command(deadline_command)
cli.add_command(priority_command)
cli.add_command(remove_dependency_command)
cli.add_command(rename_command)
cli.add_command(reopen_command)
cli.add_command(restore_command)
cli.add_command(estimate_command)
cli.add_command(schedule_command)
cli.add_command(optimize_command)
cli.add_command(stats_command)
cli.add_command(tui_command)

if __name__ == "__main__":
    cli()
