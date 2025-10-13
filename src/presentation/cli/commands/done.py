"""Done command - Mark a task as completed."""

import click

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.complete_task import CompleteTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import IncompleteChildrenError, TaskNotStartedError
from presentation.cli.batch_executor import BatchCommandExecutor
from presentation.cli.context import CliContext
from utils.console_messages import print_success


@click.command(name="done", help="Mark task(s) as completed.")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def done_command(ctx, task_ids):  # noqa: C901
    """Mark task(s) as completed."""
    ctx_obj: CliContext = ctx.obj
    console = ctx_obj.console
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    complete_task_use_case = CompleteTaskUseCase(repository, time_tracker)

    # Define processing function
    def process_task(task_id: int):
        # Check current status before completing
        task_before = repository.get_by_id(task_id)
        was_already_completed = task_before and task_before.status == TaskStatus.COMPLETED

        input_dto = CompleteTaskInput(task_id=task_id)
        result = complete_task_use_case.execute(input_dto)

        # Add marker to result for warning message
        result._was_already_completed = was_already_completed
        return result

    # Define success callback
    def on_success(task):
        print_success(console, "Completed", task)

        # Show warning if already completed
        if hasattr(task, "_was_already_completed") and task._was_already_completed:
            console.print(
                f"  [yellow]⚠[/yellow] Task was already COMPLETED (completed at [blue]{
                    task.actual_end
                }[/blue])"
            )
            return

        # Show completion time and duration if available
        if task.actual_end:
            console.print(f"  Completed at: [blue]{task.actual_end}[/blue]")

        if task.actual_duration_hours:
            console.print(f"  Duration: [cyan]{task.actual_duration_hours}h[/cyan]")

            # Show comparison with estimate if available
            if task.estimated_duration:
                diff = task.actual_duration_hours - task.estimated_duration
                if diff > 0:
                    console.print(
                        f"  [yellow]⚠[/yellow] Took [yellow]{diff}h longer[/yellow] than estimated"
                    )
                elif diff < 0:
                    console.print(
                        f"  [green]✓[/green] Finished [green]{
                            abs(diff)
                        }h faster[/green] than estimated"
                    )
                else:
                    console.print("  [green]✓[/green] Finished exactly on estimate!")

    # Define error handler for TaskNotStartedError
    def handle_not_started(e: TaskNotStartedError):
        console.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
        console.print(
            f"  [yellow]⚠[/yellow] Task is still PENDING. Start the task first with [blue]taskdog start {e.task_id}[/blue]"
        )

    # Define error handler for IncompleteChildrenError
    def handle_incomplete_children(e: IncompleteChildrenError):
        console.print(f"[red]✗[/red] Cannot complete task {e.task_id}")
        console.print("  [yellow]⚠[/yellow] The following child tasks are not completed:")
        for child in e.incomplete_children:
            status_color = "blue" if child.status == TaskStatus.IN_PROGRESS else "yellow"
            console.print(
                f"    - Task {child.id}: {child.name} ([{status_color}]{child.status.value}[/{
                    status_color
                }])"
            )
        console.print("  [dim]Complete all child tasks first, then try again.[/dim]")

    # Execute batch operation
    executor = BatchCommandExecutor(console)
    executor.execute_batch(
        task_ids=task_ids,
        process_func=process_task,
        operation_name="completing task",
        success_callback=on_success,
        error_handlers={
            TaskNotStartedError: handle_not_started,
            IncompleteChildrenError: handle_incomplete_children,
        },
    )
