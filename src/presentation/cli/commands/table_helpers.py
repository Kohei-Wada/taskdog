"""Common helper functions for table-based commands (table, today, week, etc.)."""

from application.queries.filters.task_filter import TaskFilter
from application.queries.task_query_service import TaskQueryService
from domain.entities.task import Task
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.cli.context import CliContext
from presentation.renderers.rich_table_renderer import RichTableRenderer


def get_and_filter_tasks(
    repository: JsonTaskRepository,
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
    task_query_service = TaskQueryService(repository)
    return task_query_service.get_filtered_tasks(filter_obj, sort_by=sort_by, reverse=reverse)


def render_table(ctx_obj: CliContext, tasks: list[Task], fields: list[str] | None = None) -> None:
    """Render tasks as a table.

    Args:
        ctx_obj: CLI context with console writer and notes repository
        tasks: List of tasks to render
        fields: Optional list of fields to display (None = all fields)
    """
    console_writer = ctx_obj.console_writer
    notes_repository = ctx_obj.notes_repository
    renderer = RichTableRenderer(console_writer, notes_repository)
    renderer.render(tasks, fields=fields)
