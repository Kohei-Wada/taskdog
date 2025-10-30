"""Table command - Display tasks in flat table format."""

import click

from application.queries.task_query_service import TaskQueryService
from presentation.cli.commands.common_options import (
    date_range_options,
    filter_options,
    sort_options,
)
from presentation.cli.commands.filter_helpers import apply_date_range_filter, build_task_filter
from presentation.cli.commands.table_helpers import get_and_filter_tasks, render_table
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors


@click.command(
    name="table", help="Display tasks in flat table format (shows non-archived tasks by default)."
)
@click.option(
    "--fields",
    "-f",
    type=str,
    help="Comma-separated list of fields to display (e.g., 'id,name,note,priority,status'). "
    "Available: id, name, note, priority, status, depends_on, planned_start, planned_end, "
    "actual_start, actual_end, deadline, duration, created_at, tags",
)
@click.option(
    "--tag",
    "-t",
    multiple=True,
    type=str,
    help="Filter by tags (can be specified multiple times, uses OR logic)",
)
@date_range_options()
@sort_options(default_sort="id")
@filter_options()
@click.pass_context
@handle_command_errors("displaying tasks")
def table_command(ctx, all, status, sort, reverse, fields, tag, start_date, end_date):
    """Display tasks as a flat table.

    By default, shows non-archived tasks (all statuses except archived).
    Use -a/--all to show all tasks including archived.
    Use --status to filter by specific status.
    Use --start-date and --end-date to filter by date range.

    Examples:
        taskdog table                              # Show non-archived tasks
        taskdog table -a                           # Show all tasks (including archived)
        taskdog table --status archived            # Show only archived tasks
        taskdog table --status completed           # Show only completed tasks
        taskdog table -s priority -r               # Sort by priority descending
        taskdog table --fields id,name,status      # Show specific fields only
        taskdog table --start-date 2025-10-01      # Tasks with dates >= Oct 1
        taskdog table --start-date 2025-10-01 --end-date 2025-10-31  # October tasks
    """
    ctx_obj: CliContext = ctx.obj
    repository = ctx_obj.repository

    # Parse fields option (no validation - renderer handles unknown fields gracefully)
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",")]

    # Apply tag filter if specified
    if tag:
        query_service = TaskQueryService(repository)
        tasks = query_service.filter_by_tags(list(tag), match_all=False)
        # Apply status/all filter on tag-filtered tasks
        filter_obj = build_task_filter(all=all, status=status)
        if filter_obj:
            tasks = filter_obj.filter(tasks)
        # Apply sorting
        from application.sorters.task_sorter import TaskSorter

        sorter = TaskSorter()
        tasks = sorter.sort(tasks, sort, reverse)
    else:
        # Apply filter based on options (priority: --status > --all > default)
        filter_obj = build_task_filter(all=all, status=status)
        # Get filtered and sorted tasks
        tasks = get_and_filter_tasks(repository, filter_obj, sort_by=sort, reverse=reverse)

    # Apply date range filter if specified
    tasks = apply_date_range_filter(tasks, start_date, end_date)

    # Render and display
    render_table(ctx_obj, tasks, fields=field_list)
