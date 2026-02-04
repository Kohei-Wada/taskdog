"""Custom events for TUI components."""

from datetime import date

from textual.message import Message

# Task operation events (posted by commands)


class TaskUpdated(Message):
    """Event sent when a task is updated.

    This allows widgets to react to task changes without
    direct coupling between components.

    Attributes:
        task_id: ID of the updated task
    """

    def __init__(self, task_id: int):
        """Initialize the event.

        Args:
            task_id: ID of the updated task
        """
        super().__init__()
        self.task_id = task_id


class TaskDeleted(Message):
    """Event sent when a task is deleted.

    Attributes:
        task_id: ID of the deleted task
    """

    def __init__(self, task_id: int):
        """Initialize the event.

        Args:
            task_id: ID of the deleted task
        """
        super().__init__()
        self.task_id = task_id


class TasksRefreshed(Message):
    """Event sent when the task list should be refreshed.

    This is a generic event that triggers a full reload
    of tasks from the repository.
    """

    pass


class TaskCreated(Message):
    """Event sent when a new task is created.

    Attributes:
        task_id: ID of the newly created task
    """

    def __init__(self, task_id: int):
        """Initialize the event.

        Args:
            task_id: ID of the newly created task
        """
        super().__init__()
        self.task_id = task_id


# UI interaction events (posted by widgets)


class SearchQueryChanged(Message):
    """Event sent when the search query changes.

    This allows filtering widgets to react to search input changes
    without direct coupling to the search input widget.

    Attributes:
        query: The current search query string
    """

    def __init__(self, query: str):
        """Initialize the event.

        Args:
            query: The search query string
        """
        super().__init__()
        self.query = query


class GanttResizeRequested(Message):
    """Event sent when the gantt widget needs recalculation due to resize.

    This allows the app to handle gantt recalculation with proper access
    to controllers and presenters, without the widget directly accessing them.

    Attributes:
        display_days: Number of days to display in the gantt chart
        start_date: Start date for the date range
        end_date: End date for the date range
    """

    def __init__(self, display_days: int, start_date: date, end_date: date):
        """Initialize the event.

        Args:
            display_days: Number of days to display
            start_date: Start date for gantt data
            end_date: End date for gantt data
        """
        super().__init__()
        self.display_days = display_days
        self.start_date = start_date
        self.end_date = end_date


class FilterChanged(Message):
    """Event sent when the search filter state changes.

    This allows widgets to react to filter changes and refresh their display
    with filtered data from TUIState.

    Attributes:
        query: The current search query string (may be empty)
        is_cleared: Whether the filter was just cleared
    """

    def __init__(self, query: str = "", is_cleared: bool = False):
        """Initialize the event.

        Args:
            query: The current search query string
            is_cleared: Whether the filter was just cleared
        """
        super().__init__()
        self.query = query
        self.is_cleared = is_cleared
