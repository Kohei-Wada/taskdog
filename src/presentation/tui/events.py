"""Custom events for TUI components."""

from textual.message import Message

from domain.entities.task import Task


class TaskUpdated(Message):
    """Event sent when a task is updated.

    This allows widgets to react to task changes without
    direct coupling between components.

    Attributes:
        task: The updated task
    """

    def __init__(self, task: Task):
        """Initialize the event.

        Args:
            task: The updated task
        """
        super().__init__()
        self.task = task


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
        task: The newly created task
    """

    def __init__(self, task: Task):
        """Initialize the event.

        Args:
            task: The newly created task
        """
        super().__init__()
        self.task = task
