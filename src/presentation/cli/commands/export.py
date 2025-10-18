"""Export command - Export tasks to various formats."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext
from presentation.exporters import CsvTaskExporter, JsonTaskExporter

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


@click.command(name="export", help="Export tasks to various formats.")
@click.option(
    "--format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Output format (default: json).",
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

    Supports JSON and CSV formats. More formats (Markdown, iCalendar)
    may be added in future versions.

    Examples:
        taskdog export                              # Print JSON to stdout (all fields)
        taskdog export -o tasks.json                # Save JSON to file (all fields)
        taskdog export --format csv -o tasks.csv    # Export to CSV
        taskdog export --fields id,name,priority    # Export only specific fields
        taskdog export -f id,name,status --format csv -o out.csv  # CSV with specific fields
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

        # Create appropriate exporter based on format
        if format == "json":
            exporter = JsonTaskExporter(field_list=field_list)
        elif format == "csv":
            exporter = CsvTaskExporter(field_list=field_list)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Export tasks
        tasks_data = exporter.export(tasks)

        # Output to file or stdout
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(tasks_data)
            console_writer.success(f"Exported {len(tasks)} tasks to {output}")
        else:
            print(tasks_data)

    except Exception as e:
        console_writer.error("exporting tasks", e)
        raise click.Abort() from e
