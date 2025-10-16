"""Schedule command - Set planned schedule for a task."""

import click

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.update_task import UpdateTaskUseCase
from domain.constants import DEFAULT_START_HOUR
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(name="schedule", help="Set planned schedule for a task.")
@click.argument("task_id", type=int)
@click.argument("start", type=DateTimeWithDefault(default_hour=DEFAULT_START_HOUR))
@click.argument("end", type=DateTimeWithDefault(), required=False)
@click.pass_context
@handle_task_errors("setting schedule")
def schedule_command(ctx, task_id, start, end):
    """Set planned schedule for a task.

    Usage:
        taskdog schedule <TASK_ID> <START> [END]

    Date formats:
        START: YYYY-MM-DD, MM-DD, or MM/DD (defaults to 09:00:00)
        END: YYYY-MM-DD, MM-DD, or MM/DD (defaults to 18:00:00)

    Examples:
        taskdog schedule 5 10-15
        taskdog schedule 5 2025-10-15 2025-10-17
        taskdog schedule 5 "2025-10-15 09:00:00" "2025-10-17 18:00:00"
    """
    ctx_obj: CliContext = ctx.obj
    update_task_use_case = UpdateTaskUseCase(ctx_obj.repository, ctx_obj.time_tracker)

    # Build input DTO
    input_dto = UpdateTaskInput(
        task_id=task_id,
        planned_start=start,
        planned_end=end,
    )

    # Execute use case
    task, _updated_fields = update_task_use_case.execute(input_dto)

    # Print success
    ctx_obj.console_writer.print(
        f"[green]✓[/green] Set schedule for [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan]):"
    )
    if start:
        ctx_obj.console_writer.print(f"  Start: [green]{start}[/green]")
    if end:
        ctx_obj.console_writer.print(f"  End: [green]{end}[/green]")
