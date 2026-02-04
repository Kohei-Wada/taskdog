"""Task search and filtering logic."""

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.formatters.duration_formatter import DurationFormatter
from taskdog.tui.widgets.search_query_parser import (
    SearchQueryParser,
    SearchToken,
    TokenType,
)
from taskdog.view_models.task_view_model import TaskRowViewModel

# Constants for search keywords
SEARCH_KEYWORD_FIXED = "fixed"
SEARCH_SYMBOL_FIXED = "📌"


class TaskSearchFilter:
    """Handles task search and filtering with smart case matching.

    Smart case: case-insensitive if query is all lowercase,
    case-sensitive if query contains any uppercase letters.

    Supports fzf-style exclusion syntax:
    - !term: exclude tasks containing term
    - !completed: exclude finished tasks (COMPLETED/CANCELED)
    - !status:VALUE: exclude tasks with specific status
    - !tag:tagname: exclude tasks with specific tag

    Formatters are cached at instance level to avoid repeated instantiation.
    """

    def __init__(self) -> None:
        """Initialize with cached formatters for efficient reuse."""
        self._duration_formatter = DurationFormatter()
        self._date_formatter = DateTimeFormatter()
        self._query_parser = SearchQueryParser()

    def filter(
        self, view_models: list[TaskRowViewModel], query: str
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

        # Parse query into tokens
        tokens = self._query_parser.parse(query)
        if not tokens:
            return view_models

        # Smart case: case-sensitive if query has uppercase
        case_sensitive = self._is_case_sensitive(query)

        filtered = []
        for vm in view_models:
            if self._matches_all_tokens(vm, tokens, case_sensitive):
                filtered.append(vm)

        return filtered

    def matches(
        self, task_vm: TaskRowViewModel, query: str, case_sensitive: bool | None = None
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

        # Parse query into tokens
        tokens = self._query_parser.parse(query)
        if not tokens:
            return True

        # Determine case sensitivity if not explicitly provided
        if case_sensitive is None:
            case_sensitive = self._is_case_sensitive(query)

        return self._matches_all_tokens(task_vm, tokens, case_sensitive)

    def _matches_all_tokens(
        self,
        task_vm: TaskRowViewModel,
        tokens: list[SearchToken],
        case_sensitive: bool,
    ) -> bool:
        """Check if task matches all tokens (AND logic).

        Args:
            task_vm: TaskRowViewModel to check
            tokens: List of parsed search tokens
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            True if task matches all tokens, False otherwise
        """
        searchable_fields = self._build_searchable_fields(task_vm)

        for token in tokens:
            if not self._matches_single_token(
                task_vm, token, searchable_fields, case_sensitive
            ):
                return False
        return True

    def _matches_single_token(
        self,
        task_vm: TaskRowViewModel,
        token: SearchToken,
        searchable_fields: list[str],
        case_sensitive: bool,
    ) -> bool:
        """Check if task matches a single token.

        Args:
            task_vm: TaskRowViewModel to check
            token: Single search token
            searchable_fields: Pre-built list of searchable text fields
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            True if task matches the token, False otherwise
        """
        if token.type == TokenType.INCLUDE:
            return self._contains_in_fields(
                token.value, searchable_fields, case_sensitive
            )

        elif token.type == TokenType.EXCLUDE:
            return not self._contains_in_fields(
                token.value, searchable_fields, case_sensitive
            )

        elif token.type == TokenType.EXCLUDE_STATUS:
            if token.value == "is_finished":
                # !completed shorthand - exclude COMPLETED and CANCELED
                return not task_vm.is_finished
            # Exclude specific status value
            return task_vm.status.value != token.value

        elif token.type == TokenType.EXCLUDE_TAG:
            # Case-insensitive tag comparison
            lower_tag = token.value.lower()
            return not any(t.lower() == lower_tag for t in task_vm.tags)

        return True

    def _contains_in_fields(
        self, value: str, searchable_fields: list[str], case_sensitive: bool
    ) -> bool:
        """Check if value is contained in any searchable field.

        Args:
            value: Value to search for
            searchable_fields: List of searchable text fields
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            True if value found in any field, False otherwise
        """
        search_value = value if case_sensitive else value.lower()

        for field in searchable_fields:
            if not field:
                continue
            search_field = field if case_sensitive else field.lower()
            if search_value in search_field:
                return True
        return False

    def _build_searchable_fields(self, task_vm: TaskRowViewModel) -> list[str]:
        """Build list of searchable text fields from task ViewModel.

        Extracts all visible fields that should be searchable, including
        formatted versions of duration and deadline.

        Args:
            task_vm: TaskRowViewModel to extract searchable fields from

        Returns:
            List of searchable text strings
        """
        # Core fields always included (using cached formatters)
        searchable_fields = [
            str(task_vm.id),
            task_vm.name,
            task_vm.status.value,
            str(task_vm.priority),
            self._duration_formatter.format_hours(task_vm.estimated_duration),
            self._date_formatter.format_deadline(task_vm.deadline),
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

    def _is_case_sensitive(self, query: str) -> bool:
        """Determine if query should use case-sensitive matching (smart case).

        Smart case: case-sensitive if query contains any uppercase letter,
        case-insensitive otherwise.

        Args:
            query: Search query string

        Returns:
            True if case-sensitive matching should be used, False otherwise
        """
        return any(c.isupper() for c in query)
