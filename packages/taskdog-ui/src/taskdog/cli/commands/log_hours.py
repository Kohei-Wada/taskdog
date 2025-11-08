"""Log-hours command - Log actual hours worked on a task."""

import click

from taskdog.cli.context import CliContext
from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


@click.command(
    name="log-hours", help="Log actual hours worked on a task for a specific date."
)
@click.argument("task_id", type=int)
@click.argument("hours", type=float)
@click.option(
    "--date",
    "-d",
    type=str,
    default=None,
    help="Date in YYYY-MM-DD format (default: today)",
)
@click.pass_context
def log_hours_command(ctx, task_id, hours, date):
    """Log actual hours worked on a task.

    Usage:
        taskdog log-hours <TASK_ID> <HOURS> [--date YYYY-MM-DD]

    Examples:
        taskdog log-hours 5 3.5              # Log 3.5 hours today
        taskdog log-hours 5 4 --date 2025-01-15   # Log 4 hours on specific date
        taskdog log-hours 5 2.5 -d 2025-01-14     # Short form
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Default to today if no date specified
    if date is None:
        from datetime import datetime

        date = DateTimeFormatter.format_date_only(datetime.now())

    try:
        # Log hours via API client
        task = ctx_obj.api_client.log_hours(task_id, hours, date)

        console_writer.success(f"Logged {hours}h for task {task_id} on {date}")

        # Show total logged hours for this task
        total_hours = sum(task.actual_daily_hours.values())
        console_writer.info(f"Total logged hours for task {task_id}: {total_hours}h")

    except TaskNotFoundException as e:
        console_writer.validation_error(str(e))

    except TaskValidationError as e:
        console_writer.validation_error(str(e))

    except Exception as e:
        console_writer.error("logging hours", e)
