"""Show command - Display task details and notes."""

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_task_errors
from taskdog.renderers.rich_detail_renderer import RichDetailRenderer


@click.command(name="show", help="Show task details and notes with markdown rendering.")
@click.argument("task_id", type=int)
@click.option("--raw", is_flag=True, help="Show raw markdown instead of rendered")
@click.pass_context
@handle_task_errors("showing task")
def show_command(ctx, task_id, raw):
    """Show task details and notes with rich formatting."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer

    # Get task detail via API client
    detail = ctx_obj.api_client.get_task_detail(task_id)

    # Render and display using renderer
    renderer = RichDetailRenderer(console_writer)
    renderer.render(detail, raw=raw)
