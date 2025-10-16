"""Export command - Export tasks to various formats."""

import json

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext

# Valid fields for export
VALID_FIELDS = {
    "id",
    "name",
    "priority",
    "status",
    "timestamp",
    "planned_start",
    "planned_end",
    "deadline",
    "actual_start",
    "actual_end",
    "estimated_duration",
    "daily_allocations",
}


@click.command(name="export", help="Export tasks to various formats (currently JSON only).")
@click.option(
    "--format",
    type=click.Choice(["json"]),
    default="json",
    help="Output format (default: json). More formats coming soon.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: stdout).",
)
@click.option(
    "--fields",
    "-f",
    type=str,
    help="Comma-separated list of fields to export (e.g., 'id,name,priority,status'). "
    "Available: id, name, priority, status, timestamp, planned_start, planned_end, "
    "deadline, actual_start, actual_end, estimated_duration, daily_allocations",
)
@click.pass_context
def export_command(ctx, format, output, fields):
    """Export all tasks in the specified format.

    Currently supports JSON format only. More formats (CSV, Markdown, iCalendar)
    will be added in future versions.

    Examples:
        taskdog export                              # Print JSON to stdout (all fields)
        taskdog export -o tasks.json                # Save JSON to file (all fields)
        taskdog export --fields id,name,priority    # Export only specific fields
        taskdog export -f status,deadline -o out.json  # Specific fields to file
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    console_writer = ctx_obj.console_writer
    task_query_service = TaskQueryService(repository)

    try:
        # Get all tasks (no filter)
        tasks = task_query_service.get_filtered_tasks(None)

        # Parse fields option
        field_list = None
        if fields:
            # Split by comma and strip whitespace
            field_list = [f.strip() for f in fields.split(",")]

            # Validate field names
            invalid_fields = [f for f in field_list if f not in VALID_FIELDS]
            if invalid_fields:
                valid_fields_str = ", ".join(sorted(VALID_FIELDS))
                raise ValueError(
                    f"Invalid field(s): {', '.join(invalid_fields)}. "
                    f"Valid fields are: {valid_fields_str}"
                )

        if format == "json":
            if field_list:
                # Export only selected fields
                tasks_data = json.dumps(
                    [_filter_fields(task.to_dict(), field_list) for task in tasks],
                    indent=4,
                    ensure_ascii=False,
                )
            else:
                # Export all fields
                tasks_data = json.dumps(
                    [task.to_dict() for task in tasks], indent=4, ensure_ascii=False
                )
        else:
            # Future formats will be handled here
            raise ValueError(f"Unsupported format: {format}")

        # Output to file or stdout
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(tasks_data)
            console_writer.print(
                f"[green]✓[/green] Exported {len(tasks)} tasks to [cyan]{output}[/cyan]"
            )
        else:
            print(tasks_data)

    except Exception as e:
        console_writer.error("exporting tasks", e)
        raise click.Abort() from e


def _filter_fields(task_dict: dict, fields: list[str]) -> dict:
    """Filter task dictionary to include only specified fields.

    Args:
        task_dict: Full task dictionary
        fields: List of field names to include

    Returns:
        Filtered dictionary with only specified fields
    """
    return {field: task_dict.get(field) for field in fields}
