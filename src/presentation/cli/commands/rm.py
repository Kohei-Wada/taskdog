"""Rm command - Remove a task."""

import click

from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from presentation.controllers.task_controller import TaskController


@click.command(
    name="rm", help="Remove task(s) (archive by default, --hard for permanent deletion)."
)
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.option(
    "--hard",
    is_flag=True,
    help="Permanently delete the task(s) instead of archiving.",
)
@click.pass_context
def rm_command(ctx, task_ids, hard):
    """Remove task(s).

    By default, tasks are archived (is_archived flag set to True) and can be restored with 'taskdog restore'.
    Tasks can be archived from any status (soft delete) while preserving their original status.
    Use --hard flag to permanently delete tasks from the database.
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    config = ctx_obj.config
    controller = TaskController(repository, time_tracker, config)

    def remove_single_task(task_id: int) -> None:
        if hard:
            # Hard delete: permanently remove from database
            controller.remove_task(task_id)
            console_writer.success(f"Permanently deleted task with ID: {task_id}")
        else:
            # Archive: set is_archived flag (preserves original status)
            task = controller.archive_task(task_id)
            # Use task_success to avoid Rich-specific markup
            console_writer.task_success("Archived (status preserved)", task)
            console_writer.info(f"Use 'taskdog restore {task_id}' to restore this task.")

    execute_batch_operation(task_ids, remove_single_task, console_writer, "removing task")
