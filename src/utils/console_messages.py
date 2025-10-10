"""Console message formatting utilities for taskdog commands."""

from domain.entities.task import Task


def print_success(console, action: str, task: Task) -> None:
    """Print success message with task info.

    Args:
        console: Rich Console instance
        action: Action verb (e.g., "Added", "Started", "Completed", "Updated")
        task: Task object
    """
    console.print(
        f"[green]✓[/green] {action} task: [bold]{task.name}[/bold] (ID: [cyan]{task.id}[/cyan])"
    )


def print_task_not_found_error(console, task_id: int, is_parent: bool = False) -> None:
    """Print task not found error.

    Args:
        console: Rich Console instance
        task_id: ID of the task that was not found
        is_parent: Whether this is a parent task error
    """
    prefix = "Parent task" if is_parent else "Task"
    console.print(f"[red]✗[/red] Error: {prefix} {task_id} not found", style="red")


def print_error(console, action: str, error: Exception) -> None:
    """Print general error message.

    Args:
        console: Rich Console instance
        action: Action being performed (e.g., "adding task", "starting task")
        error: Exception object
    """
    console.print(f"[red]✗[/red] Error {action}: {error}", style="red")
