"""Rendering helper for table-based commands."""

from domain.entities.task import Task
from presentation.cli.context import CliContext
from presentation.mappers.task_mapper import TaskMapper
from presentation.renderers.rich_table_renderer import RichTableRenderer


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
