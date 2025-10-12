"""Template generator for task notes markdown files."""

from datetime import datetime

from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task


def generate_notes_template(task: Task) -> str:
    """Generate markdown template for task notes.

    Args:
        task: Task entity to generate template for

    Returns:
        Markdown template string with task information
    """
    now = datetime.now().strftime(DATETIME_FORMAT)

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
