"""Start command - Start working on a task."""

import click

from application.dto.start_task_input import StartTaskInput
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import TaskStatus
from presentation.cli.commands.batch_helpers import execute_batch_operation
from presentation.cli.context import CliContext
from shared.constants import StatusVerbs


@click.command(name="start", help="Start working on task(s) (sets status to IN_PROGRESS).")
@click.argument("task_ids", nargs=-1, type=int, required=True)
@click.pass_context
def start_command(ctx, task_ids):
    """Start working on tasks (set status to IN_PROGRESS)."""
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository
    time_tracker = ctx_obj.time_tracker
    start_task_use_case = StartTaskUseCase(repository, time_tracker)

    def start_single_task(task_id: int) -> None:
        # Check current status before starting
        task_before = repository.get_by_id(task_id)
        was_already_in_progress = task_before and task_before.status == TaskStatus.IN_PROGRESS

        input_dto = StartTaskInput(task_id=task_id)
        task = start_task_use_case.execute(input_dto)

        # Print success message
        console_writer.task_success(StatusVerbs.STARTED, task)
        console_writer.task_start_time(task, was_already_in_progress)

    execute_batch_operation(task_ids, start_single_task, console_writer, "start")
