"""CLI context for dependency injection."""

from dataclasses import dataclass

from rich.console import Console

from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


@dataclass
class CliContext:
    """Context object for CLI commands containing shared dependencies.

    Attributes:
        console: Rich Console instance for output
        repository: Task repository for data access
        time_tracker: Time tracker for recording timestamps
    """

    console: Console
    repository: TaskRepository
    time_tracker: TimeTracker
