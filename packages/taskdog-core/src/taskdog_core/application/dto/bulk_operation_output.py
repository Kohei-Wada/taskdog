"""Output DTOs for bulk task operations."""

from dataclasses import dataclass

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput


@dataclass
class BulkTaskResultOutput:
    """Result for a single task in a bulk operation."""

    task_id: int
    success: bool
    task: TaskOperationOutput | None
    error: str | None
    old_status: str | None = None
    task_name: str | None = None


@dataclass
class BulkOperationOutput:
    """Output DTO for bulk task operations."""

    results: list[BulkTaskResultOutput]

    @property
    def failure_count(self) -> int:
        """Number of results that did not succeed."""
        return sum(1 for result in self.results if not result.success)

    @property
    def has_failures(self) -> bool:
        """True if any result in the batch failed."""
        return self.failure_count > 0
