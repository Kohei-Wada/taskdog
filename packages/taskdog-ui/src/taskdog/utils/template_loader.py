"""Template loader for custom note templates."""

import os
from datetime import datetime

from taskdog.infrastructure.cli_config_manager import CliConfig
from taskdog_core.application.dto.task_dto import TaskDetailDto


def load_note_template(config: CliConfig | None, task: TaskDetailDto) -> str | None:
    """Load custom note template from file and expand variables.

    Args:
        config: CLI configuration containing template path
        task: Task DTO for variable expansion

    Returns:
        Expanded template string, or None if no custom template configured/found
    """
    if config is None or config.notes.template is None:
        return None

    template_path = os.path.expanduser(config.notes.template)

    if not os.path.isfile(template_path):
        return None

    try:
        with open(template_path, encoding="utf-8") as f:
            template = f.read()
        return _expand_template_variables(template, task)
    except (OSError, UnicodeDecodeError):
        # If file can't be read, fall back to system default
        return None


def _expand_template_variables(template: str, task: TaskDetailDto) -> str:
    """Expand {{variable}} placeholders in template.

    Supported variables:
        {{task_id}} - Task ID
        {{task_name}} - Task name
        {{priority}} - Priority value
        {{status}} - Task status
        {{deadline}} - Deadline (empty string if not set)
        {{estimated_duration}} - Estimated duration in hours (empty if not set)
        {{tags}} - Comma-separated tags (empty if none)
        {{created_at}} - Current datetime

    Args:
        template: Template string with {{variable}} placeholders
        task: Task DTO for variable values

    Returns:
        Template with variables expanded
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Format optional fields
    deadline_str = ""
    if task.deadline:
        deadline_str = task.deadline.strftime("%Y-%m-%d")

    estimated_str = ""
    if task.estimated_duration is not None:
        estimated_str = str(task.estimated_duration)

    tags_str = ", ".join(task.tags) if task.tags else ""

    # Variable mapping
    variables = {
        "{{task_id}}": str(task.id),
        "{{task_name}}": task.name,
        "{{priority}}": str(task.priority),
        "{{status}}": task.status.value,
        "{{deadline}}": deadline_str,
        "{{estimated_duration}}": estimated_str,
        "{{tags}}": tags_str,
        "{{created_at}}": now,
    }

    result = template
    for placeholder, value in variables.items():
        result = result.replace(placeholder, value)

    return result
