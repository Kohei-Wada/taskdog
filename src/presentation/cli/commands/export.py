"""Export command - Export tasks to various formats."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.commands.common_options import date_range_options, filter_options
from presentation.cli.commands.filter_helpers import build_task_filter, parse_field_list
from presentation.cli.context import CliContext
from presentation.exporters import CsvTaskExporter, JsonTaskExporter, MarkdownTableExporter

# Valid fields for export
VALID_FIELDS = {
    "id",
    "name",
    "priority",
    "status",
    "created_at",
    "planned_start",
    "planned_end",
    "deadline",
    "actual_start",
    "actual_end",
    "estimated_duration",
    "daily_allocations",
}


@click.command(
    name="export",
    help="Export tasks to various formats (exports non-archived tasks by default).",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "markdown"]),
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
    "Available: id, name, priority, status, created_at, planned_start, planned_end, "
    "deadline, actual_start, actual_end, estimated_duration, daily_allocations",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Filter by tags (can be specified multiple times, uses OR logic)",
)
@date_range_options()
@filter_options()
@click.pass_context
def export_command(ctx, format, output, fields, tag, all, status, start_date, end_date):
    """Export tasks in the specified format.

    By default, exports non-archived tasks (all statuses except archived).
    Use -a/--all to export all tasks (including archived).
    Use --status to filter by specific status.
    Use --tag to filter by tags (OR logic when multiple tags specified).
    Use --start-date and --end-date to filter by date range.

    Supports JSON, CSV, and Markdown table formats.

    Examples:
        taskdog export                              # Export non-archived tasks as JSON
        taskdog export -a                           # Export all tasks (including archived)
        taskdog export --status completed           # Export only completed tasks
        taskdog export -t work -t urgent            # Export tasks with tag "work" OR "urgent"
        taskdog export -o tasks.json                # Save JSON to file
        taskdog export --format csv -o tasks.csv    # Export to CSV
        taskdog export --format markdown -o tasks.md  # Export to Markdown table
        taskdog export --fields id,name,priority    # Export only specific fields
        taskdog export -f id,name,status --format markdown  # Markdown with specific fields
        taskdog export -a --status archived -o archived.json      # Export all archived tasks
        taskdog export --start-date 2025-10-01 --end-date 2025-10-31  # October tasks
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    console_writer = ctx_obj.console_writer
    task_query_service = TaskQueryService(repository)

    try:
        # Build integrated filter with all options (tags use OR logic by default)
        tags = list(tag) if tag else None
        filter_obj = build_task_filter(
            all=all,
            status=status,
            tags=tags,
            match_all=False,  # OR logic for multiple tags
            start_date=start_date,
            end_date=end_date,
        )
        tasks = task_query_service.get_filtered_tasks(filter_obj)

        # Parse and validate fields option
        field_list = parse_field_list(fields, valid_fields=VALID_FIELDS)

        # Create appropriate exporter based on format
        if format == "json":
            exporter = JsonTaskExporter(field_list=field_list)
        elif format == "csv":
            exporter = CsvTaskExporter(field_list=field_list)
        elif format == "markdown":
            exporter = MarkdownTableExporter(field_list=field_list)
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
