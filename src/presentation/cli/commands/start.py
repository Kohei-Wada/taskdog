"""Start command - Start working on a task."""

import click

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskAlreadyFinishedError, TaskWithChildrenError
from presentation.cli.batch_executor import BatchCommandExecutor
from presentation.cli.context import CliContext
from utils.console_messages import print_success


@click.command(name="start", help="Start working on task(s) (sets status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    start_task_use_case = StartTaskUseCase(repository, time_tracker)

    # Define processing function
    def process_task(task_id: int):
        # Check current status before starting
        task_before = repository.get_by_id(task_id)
        was_already_in_progress = task_before and task_before.status == TaskStatus.IN_PROGRESS

        input_dto = StartTaskInput(task_id=task_id)
        result = start_task_use_case.execute(input_dto)

        # Add marker to result for warning message
        result._was_already_in_progress = was_already_in_progress
        return result

    # Define success callback
    def on_success(task):
        print_success(console, "Started", task)
        if hasattr(task, "_was_already_in_progress") and task._was_already_in_progress:
            console.print(
                f"  [yellow]⚠[/yellow] Task was already IN_PROGRESS (started at [blue]{task.actual_start}[/blue])"
            )
        elif task.actual_start:
            console.print(f"  Started at: [blue]{task.actual_start}[/blue]")

    # Define error handler for TaskWithChildrenError
    def handle_task_with_children(e: TaskWithChildrenError):
        console.print(f"[red]✗[/red] Cannot start task {e.task_id}")
        console.print("  [yellow]⚠[/yellow] This task has child tasks:")
        for child in e.children:
            console.print(f"    - Task {child.id}: {child.name}")
        console.print("  [dim]Start child tasks instead. Parent will auto-start.[/dim]")

    # Define error handler for TaskAlreadyFinishedError
    def handle_already_finished(e: TaskAlreadyFinishedError):
        console.print(f"[red]✗[/red] Cannot start task {e.task_id}")
        console.print(f"  [yellow]⚠[/yellow] Task is already {e.status}")
        console.print("  [dim]Finished tasks cannot be restarted.[/dim]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="starting task",
        success_callback=on_success,
        error_handlers={
            TaskWithChildrenError: handle_task_with_children,
            TaskAlreadyFinishedError: handle_already_finished,
        },
    )
