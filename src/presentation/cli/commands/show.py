"""Show command - Display task details and notes."""

import click
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from domain.exceptions.task_exceptions import TaskNotFoundException
from utils.console_messages import print_task_not_found_error, print_error
from presentation.formatters.constants import STATUS_STYLES


def format_task_info(task) -> Table:
    """Format task basic information as a Rich table.

    Args:
        task: Task entity to format

    Returns:
        Rich Table with task information
    """
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value")

    # Basic info
    table.add_row("ID", str(task.id))
    table.add_row("Name", task.name)
    table.add_row("Priority", str(task.priority))

    # Status with color
    status_style = STATUS_STYLES.get(task.status, "white")
    table.add_row("Status", f"[{status_style}]{task.status}[/{status_style}]")

    # Parent info
    if task.parent_id:
        table.add_row("Parent ID", str(task.parent_id))

    # Timestamps
    table.add_row("Created", task.created_at_str)

    # Time management fields
    if task.planned_start:
        table.add_row("Planned Start", task.planned_start)
    if task.planned_end:
        table.add_row("Planned End", task.planned_end)
    if task.deadline:
        table.add_row("Deadline", task.deadline)
    if task.actual_start:
        table.add_row("Actual Start", task.actual_start)
    if task.actual_end:
        table.add_row("Actual End", task.actual_end)
    if task.estimated_duration:
        table.add_row("Estimated Duration", f"{task.estimated_duration}h")
    if task.actual_duration_hours:
        table.add_row("Actual Duration", f"{task.actual_duration_hours}h")

    return table


@click.command(name="show", help="Show task details and notes.")
@click.argument("task_id", type=int)
@click.option("--raw", is_flag=True, help="Show raw markdown instead of rendered")
@click.pass_context
def show_command(ctx, task_id, raw):
    """Show task details and notes with rich formatting."""
    console = ctx.obj["console"]
    repository = ctx.obj["repository"]

    try:
        # Get task from repository
        task = repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException(task_id)

        # Display task basic info
        task_info = format_task_info(task)
        panel = Panel(
            task_info,
            title=f"[bold cyan]Task #{task_id}[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)
        console.print()

        # Display notes if they exist
        notes_path = task.notes_path
        if notes_path.exists():
            notes_content = notes_path.read_text(encoding="utf-8")

            if raw:
                # Show raw markdown
                console.print("[bold cyan]Notes (raw):[/bold cyan]")
                console.print(notes_content)
            else:
                # Render markdown with Rich
                console.print("[bold cyan]Notes:[/bold cyan]")
                markdown = Markdown(notes_content)
                console.print(markdown)
        else:
            console.print(
                f"[yellow]No notes found. Use 'taskdog note {
                    task_id
                }' to create notes.[/yellow]"
            )

    except TaskNotFoundException as e:
        print_task_not_found_error(console, e.task_id)
    except Exception as e:
        print_error(console, "showing task", e)
