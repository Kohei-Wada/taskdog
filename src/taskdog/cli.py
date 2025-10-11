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

# Commands module (existing)
# from commands.add_command import add_command  # OLD (replaced)
# from commands.tree_command import tree_command  # OLD (replaced)
# from commands.table_command import table_command  # OLD (replaced)
# from commands.dump_command import dump_command  # OLD (replaced)
# from commands.remove_command import remove_command  # OLD (replaced)
# from commands.update_command import update_command  # OLD (replaced)
# from commands.start_command import start_command  # OLD (replaced)
# from commands.done_command import done_command  # OLD (replaced)
# from commands.gantt_command import gantt_command  # OLD (replaced)
# from commands.today_command import today_command  # OLD (replaced)

# New commands (Clean Architecture)
from presentation.cli.commands.today import today_command_new
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


cli.add_command(add_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(tree_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(table_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(dump_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(remove_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(update_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(start_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(done_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(gantt_command)  # NEW (Clean Architecture - replaces old)
cli.add_command(today_command_new)  # NEW (Clean Architecture - replaces old)
cli.add_command(note_command)  # NEW (notes feature)
cli.add_command(show_command)  # NEW (notes feature)

if __name__ == "__main__":
    cli()
