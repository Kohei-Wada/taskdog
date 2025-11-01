"""Custom events for TUI components."""

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


class TaskSelected(Message):
    """Event sent when a task is selected in the task table.

    This allows other widgets (e.g., detail panel, gantt chart) to
    react to task selection changes without direct coupling.

    Attributes:
        task_id: The selected task ID, or None if no task is selected
    """

    def __init__(self, task_id: int | None):
        """Initialize the event.

        Args:
            task_id: The selected task ID, or None if selection is cleared
        """
        super().__init__()
        self.task_id = task_id


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
