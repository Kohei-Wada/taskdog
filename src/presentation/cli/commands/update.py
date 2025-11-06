"""Update command - Update task properties."""

import click

from domain.entities.task import TaskStatus
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from shared.click_types.datetime_with_default import DateTimeWithDefault


@click.command(
    name="update",
    help="Update multiple task properties at once. For single-field updates, prefer specialized commands (deadline, priority, rename, estimate, schedule).",
)
@click.argument("task_id", type=int)
@click.option(
    "--priority",
    type=int,
    default=None,
    help="New priority",
)
@click.option(
    "--status",
    type=click.Choice([e.value for e in TaskStatus]),
    default=None,
    help="New status",
)
@click.option(
    "--planned-start",
    type=DateTimeWithDefault("start"),
    default=None,
    help="Planned start (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 09:00:00)",
)
@click.option(
    "--planned-end",
    type=DateTimeWithDefault(),
    default=None,
    help="Planned end (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 18:00:00)",
)
@click.option(
    "--deadline",
    type=DateTimeWithDefault(),
    default=None,
    help="Deadline (YYYY-MM-DD, MM-DD, or MM/DD; defaults to 18:00:00)",
)
@click.option(
    "--estimated-duration",
    type=float,
    default=None,
    help="Estimated duration in hours (e.g., 2.5)",
)
@click.pass_context
@handle_task_errors("updating task")
def update_command(
    ctx,
    task_id,
    priority,
    status,
    planned_start,
    planned_end,
    deadline,
    estimated_duration,
):
    """Update multiple task properties at once.

    Usage:
        taskdog update <TASK_ID> [OPTIONS]

    Examples:
        # Update multiple fields at once
        taskdog update 5 --priority 3 --deadline 2025-10-15

        # Update status and record time
        taskdog update 10 --status IN_PROGRESS

        # Update deadline and estimated duration
        taskdog update 7 --deadline 2025-10-20 --estimated-duration 4.0

    For single-field updates, prefer specialized commands:
        taskdog deadline <ID> <DATE>
        taskdog priority <ID> <PRIORITY>
        taskdog estimate <ID> <HOURS>
        taskdog schedule <ID> <START> [END]
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Convert status string to Enum if provided
    status_enum = TaskStatus(status) if status else None

    # Update task via API client
    result = ctx_obj.api_client.update_task(
        task_id=task_id,
        priority=priority,
        status=status_enum,
        planned_start=planned_start,
        planned_end=planned_end,
        deadline=deadline,
        estimated_duration=estimated_duration,
    )

    if not result.updated_fields:
        console_writer.warning(
            "No fields to update. Use --priority, --status, --planned-start, --planned-end, --deadline, or --estimated-duration"
        )
        return

    # Print updates
    console_writer.task_fields_updated(result.task, result.updated_fields)
