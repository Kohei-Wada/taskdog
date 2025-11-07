"""Task search and filtering logic."""

from taskdog.tui.widgets.task_table_row_builder import TaskTableRowBuilder
from taskdog.view_models.task_view_model import TaskRowViewModel

# Constants for search keywords
SEARCH_KEYWORD_FIXED = "fixed"
SEARCH_SYMBOL_FIXED = "📌"


class TaskSearchFilter:
    """Handles task search and filtering with smart case matching.

    Smart case: case-insensitive if query is all lowercase,
    case-sensitive if query contains any uppercase letters.
    """

    @staticmethod
    def filter(
        view_models: list[TaskRowViewModel], query: str
    ) -> list[TaskRowViewModel]:
        """Filter task ViewModels based on query using smart case matching.

        Args:
            view_models: List of task ViewModels to filter
            query: Search query string

        Returns:
            List of task ViewModels matching the query
        """
        if not query:
            return view_models

        # Smart case: case-sensitive if query has uppercase
        case_sensitive = TaskSearchFilter._is_case_sensitive(query)

        filtered = []
        for vm in view_models:
            if TaskSearchFilter.matches(vm, query, case_sensitive):
                filtered.append(vm)

        return filtered

    @staticmethod
    def matches(
        task_vm: TaskRowViewModel, query: str, case_sensitive: bool | None = None
    ) -> bool:
        """Check if a task ViewModel matches the search query.

        Searches across all visible fields: ID, name, status, priority,
        dependencies, duration, deadline, tags, and fixed status.

        Args:
            task_vm: TaskRowViewModel to check
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
        searchable_fields = TaskSearchFilter._build_searchable_fields(task_vm)

        # Check if query matches any field
        return any(contains_query(field) for field in searchable_fields)

    @staticmethod
    def _build_searchable_fields(task_vm: TaskRowViewModel) -> list[str]:
        """Build list of searchable text fields from task ViewModel.

        Extracts all visible fields that should be searchable, including
        formatted versions of duration and deadline.

        Args:
            task_vm: TaskRowViewModel to extract searchable fields from

        Returns:
            List of searchable text strings
        """
        # Core fields always included
        searchable_fields = [
            str(task_vm.id),
            task_vm.name,
            task_vm.status.value,
            str(task_vm.priority),
            TaskTableRowBuilder.format_duration(task_vm),
            TaskTableRowBuilder.format_deadline(task_vm.deadline),
        ]

        # Add dependencies if present
        if task_vm.depends_on:
            searchable_fields.append(
                ",".join(str(dep_id) for dep_id in task_vm.depends_on)
            )

        # Add tags if present
        if task_vm.tags:
            searchable_fields.extend(task_vm.tags)

        # Add fixed indicators if task is fixed
        if task_vm.is_fixed:
            searchable_fields.extend([SEARCH_KEYWORD_FIXED, SEARCH_SYMBOL_FIXED])

        return searchable_fields

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
