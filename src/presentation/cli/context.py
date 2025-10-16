"""CLI context for dependency injection."""

from dataclasses import dataclass

from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository
from presentation.console.console_writer import ConsoleWriter


@dataclass
class CliContext:
    """Context object for CLI commands containing shared dependencies.

    Attributes:
        console_writer: Console writer for output
        repository: Task repository for data access
        time_tracker: Time tracker for recording timestamps
    """

    console_writer: ConsoleWriter
    repository: TaskRepository
    time_tracker: TimeTracker
