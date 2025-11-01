"""Common helper functions for table-based commands (table, today, week, etc.)."""

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from presentation.cli.commands.filter_helpers import build_task_filter
from presentation.cli.context import CliContext
from presentation.controllers.query_controller import QueryController
from presentation.mappers.task_mapper import TaskMapper
from presentation.renderers.rich_table_renderer import RichTableRenderer


def get_and_filter_tasks(
    repository: TaskRepository,
    filter_obj: TaskFilter | None,
    sort_by: str = "id",
    reverse: bool = False,
) -> list[Task]:
    """Get tasks with filtering and sorting applied.

    Args:
        repository: Task repository
        filter_obj: Filter to apply (or None for all tasks)
        sort_by: Field to sort by
        reverse: Reverse sort order

    Returns:
        Filtered and sorted list of tasks
    """
    query_controller = QueryController(repository)
    result = query_controller.list_tasks(filter_obj=filter_obj, sort_by=sort_by, reverse=reverse)
    return result.tasks


def render_table(ctx_obj: CliContext, tasks: list[Task], fields: list[str] | None = None) -> None:
    """Render tasks as a table.

    Args:
        ctx_obj: CLI context with console writer and notes repository
        tasks: List of tasks to render
        fields: Optional list of fields to display (None = all fields)
    """
    console_writer = ctx_obj.console_writer
    notes_repository = ctx_obj.notes_repository

    # Convert tasks to ViewModels
    task_mapper = TaskMapper(notes_repository)
    task_view_models = task_mapper.to_row_view_models(tasks)

    # Render using ViewModels
    renderer = RichTableRenderer(console_writer)
    renderer.render(task_view_models, fields=fields)


def execute_time_filtered_command(
    ctx_obj: CliContext,
    time_filter: TaskFilter,
    all: bool,
    status: str | None,
    sort: str,
    reverse: bool,
) -> None:
    """Execute a time-filtered command (today, week, etc.) with common logic.

    This helper combines the common pattern used by time-based commands:
    1. Build status filter based on --all and --status options
    2. Combine time filter with status filter (AND logic)
    3. Get and sort filtered tasks
    4. Render as table

    Args:
        ctx_obj: CLI context with repository and console writer
        time_filter: Time-based filter (TodayFilter, ThisWeekFilter, etc.)
        all: If True, include all tasks (finished + incomplete)
        status: Status string for filtering (or None)
        sort: Field to sort by
        reverse: Reverse sort order

    Examples:
        >>> execute_time_filtered_command(ctx_obj, TodayFilter(), all=False, status=None, sort="deadline", reverse=False)
        # Displays incomplete tasks for today, sorted by deadline

        >>> execute_time_filtered_command(ctx_obj, ThisWeekFilter(), all=True, status="pending", sort="priority", reverse=True)
        # Displays all pending tasks for this week, sorted by priority (descending)
    """
    repository = ctx_obj.repository

    # Build status filter based on --all and --status options
    status_filter = build_task_filter(all=all, status=status)

    # Combine time filter with status filter (AND logic)
    filter_obj = CompositeFilter([status_filter, time_filter]) if status_filter else time_filter

    # Get filtered and sorted tasks
    tasks = get_and_filter_tasks(repository, filter_obj, sort_by=sort, reverse=reverse)

    # Render using shared table renderer
    render_table(ctx_obj, tasks)
