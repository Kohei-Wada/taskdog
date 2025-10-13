"""Export command - Export tasks to various formats."""

import json

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.context import CliContext
from utils.console_messages import print_error


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
@click.pass_context
def export_command(ctx, format, output):
    """Export all tasks in the specified format.

    Currently supports JSON format only. More formats (CSV, Markdown, iCalendar)
    will be added in future versions.

    Examples:
        taskdog export                    # Print JSON to stdout
        taskdog export -o tasks.json      # Save JSON to file
        taskdog export --format json      # Explicit format specification
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository
    console = ctx_obj.console
    task_query_service = TaskQueryService(repository)

    try:
        tasks = task_query_service.get_all_tasks()

        if format == "json":
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
            console.print(f"[green]✓[/green] Exported {len(tasks)} tasks to [cyan]{output}[/cyan]")
        else:
            print(tasks_data)

    except Exception as e:
        print_error(console, "exporting tasks", e)
        raise click.Abort() from e
