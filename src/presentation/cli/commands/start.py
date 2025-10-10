"""Start command - Start working on a task."""

import click
from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_success, print_task_not_found_error, print_error
from application.dto.start_task_input import StartTaskInput


@click.command(name="start", help="Start working on a task (set status to IN_PROGRESS).")
@click.argument("task_id", type=int)
@click.pass_context
def start_command(ctx, task_id):
    """Start working on a task (set status to IN_PROGRESS)."""
    console = ctx.obj["console"]
    start_task_use_case = ctx.obj["start_task_use_case"]

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
