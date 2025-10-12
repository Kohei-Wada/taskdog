"""Show command - Display task details and notes."""

import click

from application.use_cases.get_task_detail import (
    GetTaskDetailInput,
    GetTaskDetailUseCase,
)
from presentation.cli.error_handler import handle_task_errors
from presentation.formatters.rich_detail_formatter import RichDetailFormatter


@click.command(name="show", help="Show task details and notes with markdown rendering.")
@click.argument("task_id", type=int)
@click.option("--raw", is_flag=True, help="Show raw markdown instead of rendered")
@click.pass_context
@handle_task_errors("showing task")
def show_command(ctx, task_id, raw):
    """Show task details and notes with rich formatting."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]

    # Execute use case to get task detail
    use_case = GetTaskDetailUseCase(repository)
    input_dto = GetTaskDetailInput(task_id)
    detail = use_case.execute(input_dto)

    # Format and display using formatter
    formatter = RichDetailFormatter(console)
    formatter.format(detail, raw=raw)
