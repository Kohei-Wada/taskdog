"""Task search and filtering logic."""

from domain.entities.task import Task
from presentation.tui.formatters.task_table_formatter import TaskTableFormatter


class TaskSearchFilter:
    """Handles task search and filtering with smart case matching.

    Smart case: case-insensitive if query is all lowercase,
    case-sensitive if query contains any uppercase letters.
    """

    @staticmethod
    def filter(tasks: list[Task], query: str) -> list[Task]:
        """Filter tasks based on query using smart case matching.

        Args:
            tasks: List of tasks to filter
            query: Search query string

        Returns:
            List of tasks matching the query
        """
        if not query:
            return tasks

        # Smart case: case-sensitive if query has uppercase
        case_sensitive = TaskSearchFilter._is_case_sensitive(query)

        filtered = []
        for task in tasks:
            if TaskSearchFilter.matches(task, query, case_sensitive):
                filtered.append(task)

        return filtered

    @staticmethod
    def matches(task: Task, query: str, case_sensitive: bool | None = None) -> bool:
        """Check if a task matches the search query.

        Searches across all visible fields: ID, name, status, priority,
        dependencies, duration, deadline, tags, and fixed status.

        Args:
            task: Task to check
            query: Search query string
            case_sensitive: Whether to use case-sensitive matching.
                          If None, uses smart case detection.

        Returns:
            True if task matches query, False otherwise
        """
        if not query:
            return True

        # Determine case sensitivity if not explicitly provided
        if case_sensitive is None:
            case_sensitive = TaskSearchFilter._is_case_sensitive(query)

        # Prepare query for comparison
        search_query = query if case_sensitive else query.lower()

        # Helper function to check if text contains query
        def contains_query(text: str) -> bool:
            if not text:
                return False
            search_text = text if case_sensitive else text.lower()
            return search_query in search_text

        # Build searchable fields
        searchable_fields = [
            str(task.id),
            task.name,
            task.status.value,
            str(task.priority),
            TaskTableFormatter.format_duration(task),
            TaskTableFormatter.format_deadline(task.deadline),
        ]

        # Add dependencies if present
        if task.depends_on:
            searchable_fields.append(",".join(str(dep_id) for dep_id in task.depends_on))

        # Add tags if present
        if task.tags:
            searchable_fields.extend(task.tags)

        # Add fixed indicators if task is fixed
        if task.is_fixed:
            searchable_fields.extend(["fixed", "📌"])

        # Check if query matches any field
        return any(contains_query(field) for field in searchable_fields)

    @staticmethod
    def _is_case_sensitive(query: str) -> bool:
        """Determine if query should use case-sensitive matching (smart case).

        Smart case: case-sensitive if query contains any uppercase letter,
        case-insensitive otherwise.

        Args:
            query: Search query string

        Returns:
            True if case-sensitive matching should be used, False otherwise
        """
        return any(c.isupper() for c in query)
