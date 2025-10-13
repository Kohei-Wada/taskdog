"""Parent command - Set or clear task parent."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from utils.console_messages import print_validation_error


@click.command(name="parent", help="Set or clear task parent.")
@click.argument("task_id", type=int)
@click.argument("parent_id", type=int, required=False)
@click.option(
    "--clear",
    is_flag=True,
    help="Clear parent (make task a root task)",
)
@click.pass_context
@handle_task_errors("setting parent", is_parent=True)
def parent_command(ctx, task_id, parent_id, clear):
    """Set or clear parent for a task.

    Usage:
        taskdog parent <TASK_ID> <PARENT_ID>  # Set parent
        taskdog parent <TASK_ID> --clear      # Clear parent (make root task)

    Examples:
        taskdog parent 5 3      # Set task 5's parent to task 3
        taskdog parent 10 1     # Set task 10's parent to task 1
        taskdog parent 5 --clear  # Clear task 5's parent (make it a root task)
    """
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Validate arguments
    if clear and parent_id is not None:
        print_validation_error(ctx_obj.console, "Cannot specify both parent ID and --clear flag")
        return

    if not clear and parent_id is None:
        print_validation_error(ctx_obj.console, "Must specify either parent ID or --clear flag")
        return

    # Determine the parent value to set
    new_parent_id = None if clear else parent_id

    # Build input DTO
    input_dto = UpdateTaskInput(task_id=task_id, parent_id=new_parent_id)

    # Execute use case
    task, _ = update_task_use_case.execute(input_dto)

    # Print success
    if clear:
        ctx_obj.console.print(
            f"[green]✓[/green] Cleared parent for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan])"
        )
    else:
        parent_task = ctx_obj.repository.get_by_id(parent_id)
        ctx_obj.console.print(
            f"[green]✓[/green] Set parent for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]): [yellow]{parent_task.name}[/yellow] (ID: [cyan]{parent_id}[/cyan])"
        )
