"""Renderer for displaying task statistics using Rich."""

from rich.table import Table
from rich.text import Text

from application.dto.statistics_result import StatisticsResult
from domain.entities.task import Task
from presentation.console.console_writer import ConsoleWriter
from presentation.constants.table_styles import TABLE_BORDER_STYLE, TABLE_HEADER_STYLE


class RichStatisticsRenderer:
    """Renders task statistics using Rich library.

    This renderer displays comprehensive statistics in a visually appealing
    format using Rich panels and tables with color-coded information.
    """

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the renderer.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def render(self, result: StatisticsResult, focus: str = "all") -> None:
        """Render statistics result.

        Args:
            result: Statistics result to display
            focus: Section to focus on ('all', 'basic', 'time', 'estimation', 'deadline', 'priority', 'trends')
        """
        # Title
        title = Text("Task Statistics", style="bold cyan")
        self.console_writer.print(title)
        self.console_writer.empty_line()

        # Render sections based on focus
        if focus in ["all", "basic"]:
            self._render_task_statistics(result)

        if focus in ["all", "time"] and result.time_stats:
            self._render_time_statistics(result)

        if focus in ["all", "estimation"] and result.estimation_stats:
            self._render_estimation_statistics(result)

        if focus in ["all", "deadline"] and result.deadline_stats:
            self._render_deadline_statistics(result)

        if focus in ["all", "priority"]:
            self._render_priority_statistics(result)

        if focus in ["all", "trends"] and result.trend_stats:
            self._render_trend_statistics(result)

    def _render_task_statistics(self, result: StatisticsResult) -> None:
        """Render basic task statistics.

        Args:
            result: Statistics result
        """
        stats = result.task_stats

        # Create table
        table = Table(
            title="Basic Statistics",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="bold")

        # Add rows
        table.add_row("Total Tasks", str(stats.total_tasks))
        table.add_row("Pending", f"[yellow]{stats.pending_count}[/yellow]")
        table.add_row("In Progress", f"[blue]{stats.in_progress_count}[/blue]")
        table.add_row("Completed", f"[green]{stats.completed_count}[/green]")
        table.add_row("Canceled", f"[red]{stats.canceled_count}[/red]")

        # Completion rate with color coding
        rate_color = self._get_rate_color(stats.completion_rate)
        table.add_row(
            "Completion Rate",
            f"[{rate_color}]{stats.completion_rate:.1%}[/{rate_color}]",
        )

        self.console_writer.print(table)
        self.console_writer.empty_line()

    def _render_time_statistics(self, result: StatisticsResult) -> None:
        """Render time tracking statistics.

        Args:
            result: Statistics result
        """
        stats = result.time_stats
        if not stats:
            return

        # Create table
        table = Table(
            title="Time Tracking Statistics",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="bold")

        # Add rows
        table.add_row(
            "Tasks with Time Tracking", f"[green]{stats.tasks_with_time_tracking}[/green]"
        )
        table.add_row("Total Work Hours", f"[bold]{stats.total_work_hours}h[/bold]")
        table.add_row("Average Hours per Task", f"{stats.average_work_hours}h")
        table.add_row("Median Hours per Task", f"{stats.median_work_hours}h")

        if stats.longest_task:
            table.add_row(
                "Longest Task",
                f"{stats.longest_task.name} ({stats.longest_task.actual_duration_hours}h)",
            )

        if stats.shortest_task:
            table.add_row(
                "Shortest Task",
                f"{stats.shortest_task.name} ({stats.shortest_task.actual_duration_hours}h)",
            )

        self.console_writer.print(table)
        self.console_writer.empty_line()

    def _render_estimation_statistics(self, result: StatisticsResult) -> None:
        """Render estimation accuracy statistics.

        Args:
            result: Statistics result
        """
        stats = result.estimation_stats
        if not stats:
            return

        # Create table
        table = Table(
            title="Estimation Accuracy Statistics",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="bold")

        # Add rows
        table.add_row(
            "Tasks with Estimation", f"[green]{stats.total_tasks_with_estimation}[/green]"
        )

        # Accuracy rate with interpretation
        accuracy_color = self._get_estimation_accuracy_color(stats.accuracy_rate)
        accuracy_text = f"[{accuracy_color}]{stats.accuracy_rate:.0%}[/{accuracy_color}]"
        if stats.accuracy_rate < 0.9:
            accuracy_text += " [red](Overestimating)[/red]"
        elif stats.accuracy_rate > 1.1:
            accuracy_text += " [yellow](Underestimating)[/yellow]"
        else:
            accuracy_text += " [green](Accurate)[/green]"
        table.add_row("Average Accuracy", accuracy_text)

        table.add_row("Over-estimated", f"[blue]{stats.over_estimated_count}[/blue]")
        table.add_row("Under-estimated", f"[yellow]{stats.under_estimated_count}[/yellow]")
        table.add_row("Accurate (±10%)", f"[green]{stats.exact_count}[/green]")

        self.console_writer.print(table)

        # Show best/worst estimated tasks
        if stats.best_estimated_tasks:
            self.console_writer.empty_line()
            self._render_task_examples("Best Estimated Tasks", stats.best_estimated_tasks, "green")

        if stats.worst_estimated_tasks:
            self.console_writer.empty_line()
            self._render_task_examples("Worst Estimated Tasks", stats.worst_estimated_tasks, "red")

        self.console_writer.empty_line()

    def _render_deadline_statistics(self, result: StatisticsResult) -> None:
        """Render deadline compliance statistics.

        Args:
            result: Statistics result
        """
        stats = result.deadline_stats
        if not stats:
            return

        # Create table
        table = Table(
            title="Deadline Compliance Statistics",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="bold")

        # Add rows
        table.add_row("Tasks with Deadline", f"[green]{stats.total_tasks_with_deadline}[/green]")
        table.add_row("Met Deadline", f"[green]{stats.met_deadline_count}[/green]")
        table.add_row("Missed Deadline", f"[red]{stats.missed_deadline_count}[/red]")

        # Compliance rate with color
        rate_color = self._get_rate_color(stats.compliance_rate)
        table.add_row(
            "Compliance Rate",
            f"[{rate_color}]{stats.compliance_rate:.1%}[/{rate_color}]",
        )

        if stats.average_delay_days > 0:
            table.add_row("Average Delay", f"[yellow]{stats.average_delay_days} days[/yellow]")

        self.console_writer.print(table)
        self.console_writer.empty_line()

    def _render_priority_statistics(self, result: StatisticsResult) -> None:
        """Render priority distribution statistics.

        Args:
            result: Statistics result
        """
        stats = result.priority_stats

        # Create table
        table = Table(
            title="Priority Distribution Statistics",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Priority Level", style="cyan")
        table.add_column("Count", justify="right", style="bold")

        # Add rows
        table.add_row("High Priority (≥70)", f"[red]{stats.high_priority_count}[/red]")
        table.add_row("Medium Priority (30-69)", f"[yellow]{stats.medium_priority_count}[/yellow]")
        table.add_row("Low Priority (<30)", f"[green]{stats.low_priority_count}[/green]")

        # High priority completion rate
        rate_color = self._get_rate_color(stats.high_priority_completion_rate)
        table.add_row(
            "High Priority Completion",
            f"[{rate_color}]{stats.high_priority_completion_rate:.1%}[/{rate_color}]",
        )

        self.console_writer.print(table)
        self.console_writer.empty_line()

    def _render_trend_statistics(self, result: StatisticsResult) -> None:
        """Render trend statistics.

        Args:
            result: Statistics result
        """
        stats = result.trend_stats
        if not stats:
            return

        # Create table for recent completions
        table = Table(
            title="Completion Trends",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Period", style="cyan")
        table.add_column("Completed Tasks", justify="right", style="bold")

        table.add_row("Last 7 Days", f"[green]{stats.last_7_days_completed}[/green]")
        table.add_row("Last 30 Days", f"[green]{stats.last_30_days_completed}[/green]")

        self.console_writer.print(table)

        # Show monthly trend if available
        if stats.monthly_completion_trend:
            self.console_writer.empty_line()
            self._render_monthly_trend(stats.monthly_completion_trend)

        self.console_writer.empty_line()

    def _render_monthly_trend(self, monthly_trend: dict[str, int]) -> None:
        """Render monthly completion trend.

        Args:
            monthly_trend: Map of month -> completion count
        """
        # Sort by month
        sorted_months = sorted(monthly_trend.items())

        # Create table
        table = Table(
            title="Monthly Completion Trend",
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("Month", style="cyan")
        table.add_column("Completed", justify="right", style="bold green")

        for month, count in sorted_months[-6:]:  # Show last 6 months
            table.add_row(month, str(count))

        self.console_writer.print(table)

    def _render_task_examples(self, title: str, tasks: list[Task], color: str = "white") -> None:
        """Render task examples.

        Args:
            title: Section title
            tasks: List of tasks to display
            color: Color for the title
        """
        table = Table(
            title=title,
            show_header=True,
            header_style=TABLE_HEADER_STYLE,
            border_style=TABLE_BORDER_STYLE,
            show_lines=False,
        )
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Task Name")
        table.add_column("Estimated", justify="right")
        table.add_column("Actual", justify="right")
        table.add_column("Accuracy", justify="right")

        for task in tasks:
            if task.estimated_duration and task.actual_duration_hours:
                accuracy = task.actual_duration_hours / task.estimated_duration
                accuracy_str = f"{accuracy:.0%}"

                table.add_row(
                    str(task.id),
                    task.name[:30],  # Truncate long names
                    f"{task.estimated_duration}h",
                    f"{task.actual_duration_hours}h",
                    accuracy_str,
                )

        self.console_writer.print(table)

    def _get_rate_color(self, rate: float) -> str:
        """Get color for a rate value.

        Args:
            rate: Rate value (0.0 to 1.0)

        Returns:
            Color name for Rich markup
        """
        if rate >= 0.8:
            return "green"
        elif rate >= 0.5:
            return "yellow"
        else:
            return "red"

    def _get_estimation_accuracy_color(self, accuracy: float) -> str:
        """Get color for estimation accuracy.

        Args:
            accuracy: Accuracy rate (actual/estimated)

        Returns:
            Color name for Rich markup
        """
        # Good accuracy: 0.9 to 1.1 (within 10%)
        if 0.9 <= accuracy <= 1.1:
            return "green"
        # Moderate: 0.7 to 1.3
        elif 0.7 <= accuracy <= 1.3:
            return "yellow"
        # Poor: outside that range
        else:
            return "red"
