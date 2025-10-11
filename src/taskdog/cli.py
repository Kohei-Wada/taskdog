import click
import os
from pathlib import Path
from rich.console import Console
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.services.time_tracker import TimeTracker

# New Clean Architecture components
from application.queries.task_query_service import TaskQueryService
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.start_task import StartTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase

# New commands (Clean Architecture)
from presentation.cli.commands.today import today_command
from presentation.cli.commands.add import add_command
from presentation.cli.commands.start import start_command
from presentation.cli.commands.done import done_command
from presentation.cli.commands.update import update_command
from presentation.cli.commands.remove import remove_command
from presentation.cli.commands.tree import tree_command
from presentation.cli.commands.table import table_command
from presentation.cli.commands.dump import dump_command
from presentation.cli.commands.gantt import gantt_command
from presentation.cli.commands.note import note_command
from presentation.cli.commands.show import show_command


@click.group()
@click.pass_context
def cli(ctx):
    """Taskdog: Hierarchical task management CLI tool."""

    # Initialize dependencies
    # Follow XDG Base Directory specification
    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    data_dir = Path(xdg_data_home) / "taskdog"
    data_dir.mkdir(parents=True, exist_ok=True)
    tasksfile = str(data_dir / "tasks.json")

    # Core dependencies
    console = Console()
    repository = JsonTaskRepository(tasksfile)
    time_tracker = TimeTracker()

    # New Clean Architecture dependencies
    task_query_service = TaskQueryService(repository)
    create_task_use_case = CreateTaskUseCase(repository)
    start_task_use_case = StartTaskUseCase(repository, time_tracker)
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)
    update_task_use_case = UpdateTaskUseCase(repository, time_tracker)
    remove_task_use_case = RemoveTaskUseCase(repository)

    ctx.ensure_object(dict)
    ctx.obj["console"] = console
    ctx.obj["repository"] = repository
    ctx.obj["time_tracker"] = time_tracker
    ctx.obj["task_query_service"] = task_query_service
    ctx.obj["create_task_use_case"] = create_task_use_case
    ctx.obj["start_task_use_case"] = start_task_use_case
    ctx.obj["complete_task_use_case"] = complete_task_use_case
    ctx.obj["update_task_use_case"] = update_task_use_case
    ctx.obj["remove_task_use_case"] = remove_task_use_case


cli.add_command(add_command)
cli.add_command(tree_command)
cli.add_command(table_command)
cli.add_command(dump_command)
cli.add_command(remove_command)
cli.add_command(update_command)
cli.add_command(start_command)
cli.add_command(done_command)
cli.add_command(gantt_command)
cli.add_command(today_command)
cli.add_command(note_command)
cli.add_command(show_command)

if __name__ == "__main__":
    cli()
