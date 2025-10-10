from typing import List
from rich.tree import Tree
from rich.console import Console
from rich.text import Text
from domain.entities.task import Task
from presentation.formatters.rich_formatter_base import RichFormatterBase


class RichTreeFormatter(RichFormatterBase):
    """Formats tasks as a hierarchical tree structure using Rich."""

    def format_tasks(self, tasks: List[Task], repository) -> str:
        """Format tasks into a hierarchical tree structure with Rich.

        Args:
            tasks: List of all tasks
            repository: Repository instance for accessing task relationships

        Returns:
            Formatted string with tree structure
        """
        if not tasks:
            return "No tasks found."

        # Get root tasks (tasks without parents)
        root_tasks = [t for t in tasks if t.parent_id is None]

        if not root_tasks:
            return "No tasks found."

        # Create main tree
        tree = Tree("[bold cyan]Tasks[/bold cyan]")

        for task in root_tasks:
            self._add_task_to_tree(task, tree, repository)

        # Render to string
        from io import StringIO

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        console.print(tree)
        return string_io.getvalue().rstrip()

    def _add_task_to_tree(self, task: Task, parent_node, repository):
        """Recursively add a task and its children to the tree.

        Args:
            task: The task to add
            parent_node: Parent tree node
            repository: Repository for accessing children
        """
        # Create task node with color based on status
        task_label = self._format_task_label(task)
        task_node = parent_node.add(task_label)

        # Add datetime and duration info as sub-nodes
        datetime_info = self._get_datetime_info(task)
        for info in datetime_info:
            task_node.add(Text(info, style="dim"))

        # Recursively add children
        children = repository.get_children(task.id)
        for child in children:
            self._add_task_to_tree(child, task_node, repository)

    def _format_task_label(self, task: Task) -> Text:
        """Format the basic information label for a task with colors.

        Args:
            task: The task to format

        Returns:
            Rich Text object with formatted task info
        """
        status_color = self._get_status_style(task.status)

        # Build the label with colors
        label = Text()
        label.append(f"[{task.id}] ", style="bold")
        label.append(task.name, style="bold white")
        label.append(f" (P:{task.priority}, ", style="dim")
        label.append(task.status.value, style=f"bold {status_color}")
        label.append(")", style="dim")

        return label

    def _get_datetime_info(self, task: Task) -> List[str]:
        """Get datetime and duration information for a task.

        Args:
            task: The task to format

        Returns:
            List of formatted datetime/duration strings
        """
        datetime_info = []

        # Deadline
        if task.deadline:
            datetime_info.append(f"⏰ Deadline: {task.deadline}")

        # Planned time
        if task.planned_start:
            datetime_info.append(
                f"📅 Planned: {task.planned_start} - {task.planned_end or '?'}"
            )

        # Actual time
        if task.actual_start:
            datetime_info.append(
                f"✓ Actual: {task.actual_start} - {task.actual_end or 'ongoing'}"
            )

        # Duration info
        duration_line = self._format_duration_info(task)
        if duration_line:
            datetime_info.append(f"⏱  {duration_line}")

        return datetime_info

    def _format_duration_info(self, task: Task) -> str:
        """Format duration information for a task.

        Args:
            task: The task to format

        Returns:
            Formatted duration string, or empty string if no duration info
        """
        if not task.estimated_duration and not task.actual_duration_hours:
            return ""

        duration_parts = []

        if task.estimated_duration:
            duration_parts.append(f"Est: {task.estimated_duration}h")

        if task.actual_duration_hours:
            duration_parts.append(f"Actual: {task.actual_duration_hours}h")

            if task.estimated_duration:
                diff = task.actual_duration_hours - task.estimated_duration
                sign = "+" if diff > 0 else ""
                duration_parts.append(f"({sign}{diff}h)")

        return " / ".join(duration_parts)
