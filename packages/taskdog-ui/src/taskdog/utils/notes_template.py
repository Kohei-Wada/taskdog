"""Template generator for task notes markdown files."""

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.infrastructure.cli_config_manager import CliConfig
from taskdog.utils.template_loader import load_note_template
from taskdog_core.application.dto.task_dto import TaskDetailDto


def get_note_template(task: TaskDetailDto, config: CliConfig | None = None) -> str:
    """Get note template with custom template support.

    Tries to load custom template from config, falls back to system default.

    Args:
        task: Task DTO to generate template for
        config: CLI configuration containing template path (optional)

    Returns:
        Template string (custom or system default)
    """
    # Try custom template first
    custom_template = load_note_template(config, task)
    if custom_template is not None:
        return custom_template

    # Fall back to system default
    return generate_notes_template(task)


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
