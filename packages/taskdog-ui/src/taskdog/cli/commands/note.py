"""Note command - Edit task notes in markdown."""

from __future__ import annotations

import select
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

from taskdog.cli.error_handler import handle_task_errors
from taskdog.utils.note_editor import edit_task_note
from taskdog_core.domain.exceptions.task_exceptions import TaskNotFoundException

if TYPE_CHECKING:
    from taskdog_client import TaskdogApiClient

    from taskdog.cli.context import CliContext
    from taskdog.console.console_writer import ConsoleWriter
    from taskdog.infrastructure.cli_config_manager import CliConfig


def _read_content_from_source(
    content: str | None, file: str | None, console_writer: ConsoleWriter
) -> str | None:
    """Read note content from --content, --file, or stdin.

    Args:
        content: Content from --content option
        file: File path from --file option
        console_writer: Console writer for errors

    Returns:
        str | None: Content if available, None if should use editor
    """
    if content is not None:
        return content

    if file is not None:
        try:
            return Path(file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            console_writer.error("reading file", e)
            return None

    # Check stdin only if no explicit options provided
    if not sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
        stdin_content = sys.stdin.read()
        # Only use stdin content if it's non-empty
        # Empty stdin (e.g., from /dev/null) should fall back to editor mode
        if stdin_content:
            return stdin_content

    return None


def _save_content_directly(
    task_id: int,
    new_content: str,
    append: bool,
    api_client: TaskdogApiClient,
    console_writer: ConsoleWriter,
) -> None:
    """Save note content directly without opening editor.

    Args:
        task_id: Task ID
        new_content: Content to save
        append: Whether to append to existing notes
        api_client: API client
        console_writer: Console writer
    """
    if append:
        existing_content, has_notes = api_client.get_task_notes(task_id)
        if has_notes and existing_content:
            final_content = existing_content.rstrip() + "\n\n" + new_content.lstrip()
        else:
            final_content = new_content
    else:
        final_content = new_content

    if not final_content.strip():
        console_writer.warning("Note content is empty")

    try:
        api_client.update_task_notes(task_id, final_content)
        console_writer.success(f"Notes saved for task #{task_id}")
    except Exception as e:
        console_writer.error("saving notes", e)


def _edit_with_editor_via_shared(
    task_id: int,
    task: object,
    api_client: TaskdogApiClient,
    console_writer: ConsoleWriter,
    config: CliConfig | None = None,
) -> None:
    """Edit note using $EDITOR via shared note_editor utility.

    Args:
        task_id: Task ID
        task: Task detail DTO
        api_client: API client
        console_writer: Console writer
        config: CLI configuration for custom template (optional)
    """

    def on_success(name: str, tid: int) -> None:
        console_writer.success(f"Notes saved for task #{tid}")

    def on_error(action: str, e: Exception) -> None:
        if isinstance(e, RuntimeError) and "interrupted" in str(e).lower():
            print("\n")
            console_writer.warning("Editor interrupted")
        else:
            console_writer.error(action, e)

    edit_task_note(
        task=task,  # type: ignore[arg-type]
        notes_provider=api_client,
        on_success=on_success,
        on_error=on_error,
        config=config,
    )


@click.command(
    name="note",
    help="Edit task notes in markdown. Supports stdin, --content, --file, or $EDITOR.",
)
@click.argument("task_id", type=int)
@click.option(
    "--content",
    "-c",
    type=str,
    help="Note content as a string (alternative to opening editor).",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Read note content from a file (alternative to opening editor).",
)
@click.option(
    "--append",
    "-a",
    is_flag=True,
    help="Append to existing notes instead of replacing them.",
)
@click.pass_context
@handle_task_errors("editing notes")
def note_command(
    ctx: click.Context,
    task_id: int,
    content: str | None,
    file: str | None,
    append: bool,
) -> None:
    """Edit task notes in markdown.

    Supports multiple input methods:
    - stdin/pipe: echo "content" | taskdog note 123
    - --content: taskdog note 123 --content "text"
    - --file: taskdog note 123 --file notes.md
    - $EDITOR: taskdog note 123 (default, opens editor)

    Use --append to add to existing notes instead of replacing.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    api_client = ctx_obj.api_client

    # Validate: only one explicit input source allowed
    if content is not None and file is not None:
        console_writer.validation_error(
            "Cannot specify multiple input sources (--content, --file). Choose only one."
        )
        return

    # Get task from API
    result = api_client.get_task_by_id(task_id)
    if not result.task:
        raise TaskNotFoundException(task_id)
    task = result.task

    # Try to read content from sources (priority: --content, --file, stdin)
    new_content = _read_content_from_source(content, file, console_writer)

    if new_content is not None:
        # Save content directly without editor
        _save_content_directly(task_id, new_content, append, api_client, console_writer)
    else:
        # No input source, use editor mode
        _edit_with_editor_via_shared(
            task_id, task, api_client, console_writer, ctx_obj.config
        )
