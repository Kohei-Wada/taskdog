"""Rendering helper for table-based commands."""

from taskdog.cli.context import CliContext
from taskdog.presenters.table_presenter import TablePresenter
from taskdog.renderers.rich_table_renderer import RichTableRenderer
from taskdog_core.application.dto.task_list_output import TaskListOutput


def render_table(
    ctx_obj: CliContext, output: TaskListOutput, fields: list[str] | None = None
) -> None:
    """Render tasks as a table.

    Args:
        ctx_obj: CLI context with console writer and API client
        output: TaskListOutput DTO from QueryController
        fields: Optional list of fields to display (None = all fields)
    """
    console_writer = ctx_obj.console_writer

    # Convert DTO to ViewModels using Presenter
    presenter = TablePresenter()
    task_view_models = presenter.present(output)

    # Render using ViewModels
    renderer = RichTableRenderer(console_writer)
    renderer.render(task_view_models, fields=fields)
