"""Start command - Start working on a task."""

import click

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.services.time_tracker import TimeTracker
from presentation.cli.batch_executor import BatchCommandExecutor
from utils.console_messages import print_success


@click.command(name="start", help="Start working on tasks (set status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):
    """Start working on tasks (set status to IN_PROGRESS)."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]
    time_tracker = TimeTracker()
    start_task_use_case = StartTaskUseCase(repository, time_tracker)

    # Define processing function
    def process_task(task_id: int):
        input_dto = StartTaskInput(task_id=task_id)
        return start_task_use_case.execute(input_dto)

    # Define success callback
    def on_success(task):
        print_success(console, "Started", task)
        if task.actual_start:
            console.print(f"  Started at: [blue]{task.actual_start}[/blue]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="starting task",
        success_callback=on_success,
    )
