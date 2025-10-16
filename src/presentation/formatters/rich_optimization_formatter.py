"""Formatter for optimization results using Rich."""

from rich.table import Table

from application.dto.optimization_summary import OptimizationSummary
from domain.entities.task import Task, TaskStatus
from presentation.console.console_writer import ConsoleWriter


class RichOptimizationFormatter:
    """Formats optimization results with Rich tables and styled output.

    This formatter is responsible for displaying:
    - Task optimization table (modified tasks)
    - Summary statistics (new/rescheduled counts, workload, conflicts)
    - Warnings (unscheduled tasks, overloaded days)
    """

    def __init__(self, console_writer: ConsoleWriter):
        """Initialize the formatter.

        Args:
            console_writer: Console writer for output
        """
        self.console_writer = console_writer

    def format_table(
        self,
        modified_tasks: list[Task],
        task_states_before: dict[int, str | None],
    ) -> None:
        """Format and print optimization results table.

        Args:
            modified_tasks: Tasks that were optimized
            task_states_before: Mapping of task IDs to their planned_start before optimization
        """
        # Create table
        table = Table(title="Optimized Tasks")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name", style="white")
        table.add_column("Change", style="yellow")
        table.add_column("Priority", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Planned Start", style="green")
        table.add_column("Planned End", style="green")
        table.add_column("Deadline", style="red")

        # Sort by planned_start
        sorted_tasks = sorted(
            modified_tasks, key=lambda t: t.planned_start if t.planned_start else ""
        )

        for task in sorted_tasks:
            # Determine change type
            if task.id in task_states_before:
                change_type = "NEW" if task_states_before[task.id] is None else "RESCHEDULED"
            else:
                change_type = "NEW"

            # Format duration
            duration_str = f"{task.estimated_duration}h" if task.estimated_duration else "-"

            # Format dates
            start_str = task.planned_start if task.planned_start else "-"
            end_str = task.planned_end if task.planned_end else "-"
            deadline_str = task.deadline if task.deadline else "-"

            table.add_row(
                str(task.id),
                task.name,
                change_type,
                str(task.priority),
                duration_str,
                start_str,
                end_str,
                deadline_str,
            )

        self.console_writer.print(table)

    def format_summary(
        self,
        summary: OptimizationSummary,
    ) -> None:
        """Format and print summary statistics.

        Args:
            summary: Optimization summary data
        """
        self.console_writer.print("\n[bold]Summary:[/bold]")
        self.console_writer.print(f"  • {summary.new_count} task(s) newly scheduled")
        if summary.rescheduled_count > 0:
            self.console_writer.print(f"  • {summary.rescheduled_count} task(s) rescheduled (--force)")
        self.console_writer.print(
            f"  • Total workload: {summary.total_hours}h across {summary.days_span} days"
        )
        if summary.deadline_conflicts > 0:
            self.console_writer.print(f"  • [red]⚠[/red] Deadline conflicts: {summary.deadline_conflicts}")
        else:
            self.console_writer.print("  • Deadline conflicts: 0")

    def _get_unscheduled_reason(self, task: Task) -> str:
        """Determine why a task could not be scheduled.

        Args:
            task: The unscheduled task

        Returns:
            Human-readable reason string
        """
        # Check if task is in progress
        if task.status == TaskStatus.IN_PROGRESS:
            return "Currently in progress (not reschedulable)"

        # Check if task has a deadline constraint
        if task.deadline:
            return "Cannot meet deadline with current constraints"

        # Default reason - truly no available time slots
        return "No available time slots"

    def format_warnings(
        self,
        summary: OptimizationSummary,
        max_hours_per_day: float,
    ) -> None:
        """Format and print warnings (unscheduled tasks, overloaded days).

        Args:
            summary: Optimization summary data
            max_hours_per_day: Maximum hours per day constraint
        """
        # Unscheduled tasks warning
        if summary.unscheduled_tasks:
            self.console_writer.print(
                f"\n  [yellow]⚠[/yellow] {len(summary.unscheduled_tasks)} task(s) could not be scheduled:"
            )
            for task in summary.unscheduled_tasks[:5]:  # Show first 5
                reason = self._get_unscheduled_reason(task)
                self.console_writer.print(f"    • #{task.id} {task.name} - {reason}")
            if len(summary.unscheduled_tasks) > 5:
                self.console_writer.print(f"    ... and {len(summary.unscheduled_tasks) - 5} more")
            self.console_writer.print(
                "\n  [dim]Tip: Try increasing --max-hours-per-day or adjusting task deadlines[/dim]"
            )

        # Workload validation
        self.console_writer.print("\n[bold]Workload Validation:[/bold]")
        if summary.overloaded_days:
            self.console_writer.print(
                f"  [red]⚠[/red] {len(summary.overloaded_days)} day(s) exceed max hours:"
            )
            for date_str, hours in summary.overloaded_days[:5]:  # Show first 5
                self.console_writer.print(f"    • {date_str}: {hours}h (max: {max_hours_per_day}h)")
            if len(summary.overloaded_days) > 5:
                self.console_writer.print(f"    ... and {len(summary.overloaded_days) - 5} more")
        else:
            self.console_writer.print(
                f"  [green]✓[/green] All days within max hours ({max_hours_per_day}h/day)"
            )
