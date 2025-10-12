"""Start command - Start working on a task."""

import click

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from domain.services.time_tracker import TimeTracker
from utils.console_messages import print_error, print_success, print_task_not_found_error


@click.command(name="start", help="Start working on tasks (set status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):
    """Start working on tasks (set status to IN_PROGRESS)."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    start_task_use_case = StartTaskUseCase(repository, time_tracker)

    for task_id in task_ids:
        try:
            input_dto = StartTaskInput(task_id=task_id)
            task = start_task_use_case.execute(input_dto)

            print_success(console, "Started", task)
            if task.actual_start:
                console.print(f"  Started at: [blue]{task.actual_start}[/blue]")
        except TaskNotFoundException as e:
            print_task_not_found_error(console, e.task_id)
        except Exception as e:
            print_error(console, "starting task", e)
