"""Type aliases for single-task operation DTOs.

These type aliases provide semantic clarity while sharing the same
underlying SingleTaskInput structure.
"""

from taskdog_core.application.dto.base import SingleTaskInput

ArchiveTaskInput = SingleTaskInput
CancelTaskInput = SingleTaskInput
CompleteTaskInput = SingleTaskInput
PauseTaskInput = SingleTaskInput
RemoveTaskInput = SingleTaskInput
ReopenTaskInput = SingleTaskInput
RestoreTaskInput = SingleTaskInput
StartTaskInput = SingleTaskInput
