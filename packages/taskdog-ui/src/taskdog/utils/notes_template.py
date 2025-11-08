"""Template generator for task notes markdown files."""

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog_core.application.dto.task_dto import TaskDetailDto


def generate_notes_template(task: TaskDetailDto) -> str:
    """Generate markdown template for task notes.

    Args:
        task: Task DTO to generate template for

    Returns:
        Markdown template string with task information
    """
    now = DateTimeFormatter.format_current_timestamp()

    template = f"""# Task #{task.id}: {task.name}

## Overview
[Task overview]

## Details
- [ ] Subtask 1
- [ ] Subtask 2

## Technical Notes
[Technical details, references, etc.]

## Progress Log
### {now}
[Work started]
"""
    return template
