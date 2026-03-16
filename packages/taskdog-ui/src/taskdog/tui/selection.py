"""Selection provider for decoupling commands from widget types."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from taskdog.tui.app import TaskdogTUI


class SelectionProvider(Protocol):
    """Protocol for providing task selection information."""

    def get_selected_task_id(self) -> int | None: ...
    def get_selected_task_ids(self) -> list[int]: ...
    def get_explicitly_selected_task_ids(self) -> list[int]: ...
    def clear_selection(self) -> None: ...


class AppSelectionProvider:
    """Selection provider that resolves selection from the TUI app.

    Consolidates all widget-type-specific selection logic (GanttDataTable vs
    TaskTable) in one place, keeping commands decoupled from widget types.
    """

    def __init__(self, app: "TaskdogTUI") -> None:
        self._app = app

    def get_selected_task_id(self) -> int | None:
        """Get the ID of the currently selected task.

        When a GanttDataTable cell is focused, returns the task at the
        Gantt cursor row. Otherwise falls back to TaskTable selection.
        """
        from taskdog.tui.widgets.gantt_data_table import GanttDataTable

        if isinstance(self._app.focused, GanttDataTable):
            return self._app.focused.get_selected_task_id()

        if not self._app.main_screen or not self._app.main_screen.task_table:
            return None
        return self._app.main_screen.task_table.get_selected_task_id()

    def get_selected_task_ids(self) -> list[int]:
        """Get all selected task IDs for batch operations.

        When a GanttDataTable cell is focused, returns single task at cursor.
        Otherwise returns TaskTable multi-selection or cursor fallback.
        """
        from taskdog.tui.widgets.gantt_data_table import GanttDataTable

        if isinstance(self._app.focused, GanttDataTable):
            task_id = self._app.focused.get_selected_task_id()
            return [task_id] if task_id is not None else []

        if not self._app.main_screen or not self._app.main_screen.task_table:
            return []
        return self._app.main_screen.task_table.get_selected_task_ids()

    def get_explicitly_selected_task_ids(self) -> list[int]:
        """Get only explicitly selected task IDs (no cursor fallback)."""
        if not self._app.main_screen or not self._app.main_screen.task_table:
            return []
        return self._app.main_screen.task_table.get_explicitly_selected_task_ids()

    def clear_selection(self) -> None:
        """Clear all task selections in the table."""
        if not self._app.main_screen or not self._app.main_screen.task_table:
            return
        self._app.main_screen.task_table.clear_selection()
