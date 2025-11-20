"""Stats command - Display task statistics and analytics."""

import click

from taskdog.cli.context import CliContext
from taskdog.cli.error_handler import handle_command_errors
from taskdog.mappers.statistics_mapper import StatisticsMapper
from taskdog.renderers.rich_statistics_renderer import RichStatisticsRenderer


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
def stats_command(ctx: click.Context, period: str, focus: str) -> None:
    """Display task statistics and analytics."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    # Calculate statistics via API
    result = api_client.calculate_statistics(period=period)

    # Check if we have any tasks
    if result.task_stats.total_tasks == 0:
        console_writer.warning("No tasks found to analyze.")
        return

    # Convert DTO to ViewModel (Mapper applies presentation logic)
    view_model = StatisticsMapper.from_statistics_result(result)

    # Render statistics
    renderer = RichStatisticsRenderer(console_writer)
    renderer.render(view_model, focus=focus)
