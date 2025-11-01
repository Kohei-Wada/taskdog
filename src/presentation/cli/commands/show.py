"""Show command - Display task details and notes."""

import click

from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_task_errors
from presentation.controllers.task_controller import TaskController
from presentation.renderers.rich_detail_renderer import RichDetailRenderer


@click.command(name="show", help="Show task details and notes with markdown rendering.")
@click.argument("task_id", type=int)
@click.option("--raw", is_flag=True, help="Show raw markdown instead of rendered")
@click.pass_context
@handle_task_errors("showing task")
def show_command(ctx, task_id, raw):
    """Show task details and notes with rich formatting."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    config = ctx_obj.config
    notes_repository = ctx_obj.notes_repository

    # Get task detail via controller
    controller = TaskController(repository, time_tracker, config, notes_repository)
    detail = controller.get_task_detail(task_id)

    # Render and display using renderer
    renderer = RichDetailRenderer(console_writer)
    renderer.render(detail, raw=raw)
