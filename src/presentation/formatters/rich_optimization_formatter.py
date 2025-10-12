"""Formatter for optimization results using Rich."""

from rich.console import Console
from rich.table import Table

from application.dto.optimization_summary import OptimizationSummary
from domain.entities.task import Task


class RichOptimizationFormatter:
    """Formats optimization results with Rich tables and styled output.

    This formatter is responsible for displaying:
    - Task optimization table (modified tasks)
    - Summary statistics (new/rescheduled counts, workload, conflicts)
    - Warnings (unscheduled tasks, overloaded days)
    """

    def __init__(self, console: Console):
        """Initialize the formatter.

        Args:
            console: Rich Console instance for output
        """
        self.console = console

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
                if task_states_before[task.id] is None:
                    change_type = "NEW"
                else:
                    change_type = "RESCHEDULED"
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

        self.console.print(table)

    def format_summary(
        self,
        summary: OptimizationSummary,
    ) -> None:
        """Format and print summary statistics.

        Args:
            summary: Optimization summary data
        """
        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  • {summary.new_count} task(s) newly scheduled")
        if summary.rescheduled_count > 0:
            self.console.print(f"  • {summary.rescheduled_count} task(s) rescheduled (--force)")
        self.console.print(
            f"  • Total workload: {summary.total_hours}h across {summary.days_span} days"
        )
        if summary.deadline_conflicts > 0:
            self.console.print(f"  • [red]⚠[/red] Deadline conflicts: {summary.deadline_conflicts}")
        else:
            self.console.print("  • Deadline conflicts: 0")

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
            self.console.print(
                f"\n  [yellow]⚠[/yellow] {len(summary.unscheduled_tasks)} task(s) could not be scheduled:"
            )
            for task in summary.unscheduled_tasks[:5]:  # Show first 5
                reason = "No available time slots"
                if task.deadline:
                    reason = "Cannot meet deadline with current constraints"
                self.console.print(f"    • #{task.id} {task.name} - {reason}")
            if len(summary.unscheduled_tasks) > 5:
                self.console.print(f"    ... and {len(summary.unscheduled_tasks) - 5} more")
            self.console.print(
                "\n  [dim]Tip: Try increasing --max-hours-per-day or adjusting task deadlines[/dim]"
            )

        # Workload validation
        self.console.print("\n[bold]Workload Validation:[/bold]")
        if summary.overloaded_days:
            self.console.print(
                f"  [red]⚠[/red] {len(summary.overloaded_days)} day(s) exceed max hours:"
            )
            for date_str, hours in summary.overloaded_days[:5]:  # Show first 5
                self.console.print(f"    • {date_str}: {hours}h (max: {max_hours_per_day}h)")
            if len(summary.overloaded_days) > 5:
                self.console.print(f"    ... and {len(summary.overloaded_days) - 5} more")
        else:
            self.console.print(
                f"  [green]✓[/green] All days within max hours ({max_hours_per_day}h/day)"
            )
