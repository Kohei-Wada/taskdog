"""Dashboard widget for displaying task statistics."""

from dataclasses import dataclass
from datetime import datetime

from textual.widgets import Static

from domain.entities.task import Task, TaskStatus


@dataclass
class DashboardData:
    """Data structure for dashboard statistics.

    Attributes:
        total_tasks: Total number of tasks
        pending_tasks: Number of pending tasks
        in_progress_tasks: Number of in-progress tasks
        completed_tasks: Number of completed tasks
        failed_tasks: Number of failed tasks
        today_tasks: Number of tasks scheduled for today
        today_hours: Total hours planned for today
        due_soon_tasks: Number of tasks due within 3 days
        completion_rate: Percentage of completed tasks (0-100)
    """

    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    today_tasks: int
    today_hours: float
    due_soon_tasks: int
    completion_rate: float


class DashboardWidget(Static):
    """Widget for displaying task statistics and summary information."""

    def update_dashboard(self, tasks: list[Task]) -> None:
        """Update the dashboard with task statistics.

        Args:
            tasks: List of tasks to calculate statistics from
        """
        data = self._calculate_dashboard_data(tasks)
        content = self._format_dashboard(data)
        self.update(content)

    def _calculate_dashboard_data(self, tasks: list[Task]) -> DashboardData:
        """Calculate dashboard statistics from tasks.

        Args:
            tasks: List of tasks

        Returns:
            DashboardData with calculated statistics
        """
        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)

        # Calculate today's tasks
        today = datetime.now().date()
        today_tasks = []
        today_hours = 0.0

        for task in tasks:
            if task.planned_start and task.planned_end:
                try:
                    start_date = datetime.strptime(task.planned_start, "%Y-%m-%d %H:%M:%S").date()
                    end_date = datetime.strptime(task.planned_end, "%Y-%m-%d %H:%M:%S").date()
                    if start_date <= today <= end_date:
                        today_tasks.append(task)
                        if task.estimated_duration:
                            today_hours += task.estimated_duration
                except ValueError:
                    pass

        # Calculate tasks due soon (within 3 days)
        due_soon = 0
        for task in tasks:
            if task.deadline and task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                try:
                    deadline_date = datetime.strptime(task.deadline, "%Y-%m-%d %H:%M:%S").date()
                    days_until = (deadline_date - today).days
                    if 0 <= days_until <= 3:
                        due_soon += 1
                except ValueError:
                    pass

        # Calculate completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0.0

        return DashboardData(
            total_tasks=total,
            pending_tasks=pending,
            in_progress_tasks=in_progress,
            completed_tasks=completed,
            failed_tasks=failed,
            today_tasks=len(today_tasks),
            today_hours=today_hours,
            due_soon_tasks=due_soon,
            completion_rate=completion_rate,
        )

    def _format_dashboard(self, data: DashboardData) -> str:
        """Format dashboard data as Rich markup.

        Args:
            data: Dashboard data to format

        Returns:
            Formatted string with Rich markup
        """
        # Task status counts with icons and colors
        status_line = (
            f"[bold white]Tasks:[/bold white] {data.total_tasks} total  "
            f"[dim]|[/dim]  "
            f"[yellow]⏸ {data.pending_tasks} pending[/yellow]  "
            f"[dim]|[/dim]  "
            f"[blue]▶ {data.in_progress_tasks} active[/blue]  "
            f"[dim]|[/dim]  "
            f"[green]✓ {data.completed_tasks} done[/green]"
        )

        if data.failed_tasks > 0:
            status_line += f"  [dim]|[/dim]  [red]✗ {data.failed_tasks} failed[/red]"

        # Today's plan and alerts
        alerts = []
        if data.due_soon_tasks > 0:
            alerts.append(f"[red]⚠ {data.due_soon_tasks} due soon[/red]")

        today_line = (
            f"[bold white]Today:[/bold white] {data.today_tasks} tasks "
            f"[dim]({data.today_hours:.1f}h planned)[/dim]"
        )
        if alerts:
            today_line += f"  [dim]|[/dim]  {' '.join(alerts)}"

        # Progress bar
        progress_line = (
            f"[bold white]Progress:[/bold white] "
            f"{data.completion_rate:.1f}% complete "
            f"[dim]({data.completed_tasks}/{data.total_tasks})[/dim]"
        )

        return f"{status_line}\n{today_line}\n{progress_line}"
