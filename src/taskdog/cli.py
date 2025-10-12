import os
from pathlib import Path

import click
from rich.console import Console

from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.cli.commands.add import add_command
from presentation.cli.commands.archive import archive_command
from presentation.cli.commands.deadline import deadline_command
from presentation.cli.commands.done import done_command
from presentation.cli.commands.estimate import estimate_command
from presentation.cli.commands.export import export_command
from presentation.cli.commands.gantt import gantt_command
from presentation.cli.commands.note import note_command
from presentation.cli.commands.optimize import optimize_command
from presentation.cli.commands.parent import parent_command
from presentation.cli.commands.priority import priority_command
from presentation.cli.commands.rename import rename_command
from presentation.cli.commands.rm import rm_command
from presentation.cli.commands.schedule import schedule_command
from presentation.cli.commands.show import show_command
from presentation.cli.commands.start import start_command
from presentation.cli.commands.table import table_command

# Commands
from presentation.cli.commands.today import today_command
from presentation.cli.commands.tree import tree_command
from presentation.cli.commands.update import update_command
from presentation.cli.context import CliContext


@click.group()
@click.pass_context
def cli(ctx):
    """Taskdog: Hierarchical task management CLI tool."""

    # Follow XDG Base Directory specification
    xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    data_dir = Path(xdg_data_home) / "taskdog"
    data_dir.mkdir(parents=True, exist_ok=True)
    tasksfile = str(data_dir / "tasks.json")

    # Initialize shared dependencies
    console = Console()
    repository = JsonTaskRepository(tasksfile)
    time_tracker = TimeTracker()

    # Store in CliContext for type-safe access
    ctx.ensure_object(dict)
    ctx.obj = CliContext(
        console=console,
        repository=repository,
        time_tracker=time_tracker,
    )


cli.add_command(add_command)
cli.add_command(tree_command)
cli.add_command(table_command)
cli.add_command(export_command)
cli.add_command(rm_command)
cli.add_command(archive_command)
cli.add_command(update_command)
cli.add_command(start_command)
cli.add_command(done_command)
cli.add_command(gantt_command)
cli.add_command(today_command)
cli.add_command(note_command)
cli.add_command(show_command)
cli.add_command(deadline_command)
cli.add_command(priority_command)
cli.add_command(rename_command)
cli.add_command(estimate_command)
cli.add_command(schedule_command)
cli.add_command(parent_command)
cli.add_command(optimize_command)

if __name__ == "__main__":
    cli()
