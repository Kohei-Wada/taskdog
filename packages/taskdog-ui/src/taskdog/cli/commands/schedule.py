"""Schedule command - Set planned schedule for a task."""

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(name="schedule", help="Set planned schedule for a task.")
@click.argument("task_id", type=int)
@click.argument("start", type=DateTimeWithDefault("start"))
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

    # Update task via API client
    result = ctx_obj.api_client.update_task(
        task_id=task_id,
        planned_start=start,
        planned_end=end,
    )

    # Print success - format schedule as "start → end"
    def format_schedule(value) -> str:
        start_str = result.task.planned_start if result.task.planned_start else "N/A"
        end_str = result.task.planned_end if result.task.planned_end else "N/A"
        return f"{start_str} → {end_str}"

    ctx_obj.console_writer.update_success(
        result.task, "schedule", result.task, format_schedule
    )
