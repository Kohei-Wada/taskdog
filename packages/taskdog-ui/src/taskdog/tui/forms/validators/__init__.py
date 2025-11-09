"""Common validation logic for TUI forms."""

from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult
from taskdog.tui.forms.validators.collection_validators import (
    DependenciesValidator,
    TagsValidator,
)
from taskdog.tui.forms.validators.datetime_validator import DateTimeValidator
from taskdog.tui.forms.validators.duration_validator import DurationValidator
from taskdog.tui.forms.validators.task_validators import (
    PriorityValidator,
    TaskNameValidator,
)

__all__ = [
    "BaseValidator",
    "DateTimeValidator",
    "DependenciesValidator",
    "DurationValidator",
    "PriorityValidator",
    "TagsValidator",
    "TaskNameValidator",
    "ValidationResult",
]
