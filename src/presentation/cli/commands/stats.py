"""Stats command - Display task statistics and analytics."""

import click

from application.dto.statistics_result import CalculateStatisticsInput
from application.use_cases.calculate_statistics import CalculateStatisticsUseCase
from presentation.cli.context import CliContext
from presentation.cli.error_handler import handle_command_errors
from presentation.renderers.rich_statistics_renderer import RichStatisticsRenderer


@click.command(
    name="stats",
    help="""Display task statistics and analytics.

Shows comprehensive statistics including basic counts, time tracking,
estimation accuracy, deadline compliance, priority distribution, and trends.

Use --period to filter by time period and --focus to show specific sections.
""",
)
@click.option(
    "--period",
    "-p",
    type=click.Choice(["all", "7d", "30d"], case_sensitive=False),
    default="all",
    help="Time period for filtering tasks (default: all)",
)
@click.option(
    "--focus",
    "-f",
    type=click.Choice(
        ["all", "basic", "time", "estimation", "deadline", "priority", "trends"],
        case_sensitive=False,
    ),
    default="all",
    help="Focus on specific statistics section (default: all)",
)
@click.pass_context
@handle_command_errors("calculating statistics")
def stats_command(ctx, period, focus):
    """Display task statistics and analytics."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    # Execute use case
    use_case = CalculateStatisticsUseCase(repository)
    result = use_case.execute(CalculateStatisticsInput(period=period))

    # Check if we have any tasks
    if result.task_stats.total_tasks == 0:
        console_writer.warning("No tasks found to analyze.")
        return

    # Render statistics
    renderer = RichStatisticsRenderer(console_writer)
    renderer.render(result, focus=focus)
