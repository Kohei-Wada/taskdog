"""Remove-dependency command - Remove a task dependency."""

import click

from application.dto.manage_dependencies_input import RemoveDependencyInput
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from presentation.cli.context import CliContext


@click.command(name="remove-dependency", help="Remove a dependency from a task.")
@click.argument("task_id", type=int)
@click.argument("depends_on_id", type=int)
@click.pass_context
def remove_dependency_command(ctx, task_id, depends_on_id):
    """Remove a dependency from a task.

    Usage:
        taskdog remove-dependency <TASK_ID> <DEPENDS_ON_ID>

    Examples:
        taskdog remove-dependency 5 3    # Remove task 3 from task 5's dependencies
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    try:
        input_dto = RemoveDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        use_case = RemoveDependencyUseCase(repository)
        task = use_case.execute(input_dto)

        console_writer.success(
            f"Removed dependency: Task {task_id} no longer depends on task {depends_on_id}"
        )
        console_writer.info(f"Task {task_id} dependencies: {task.depends_on}")

    except TaskNotFoundException as e:
        console_writer.validation_error(str(e))

    except TaskValidationError as e:
        console_writer.validation_error(str(e))

    except Exception as e:
        console_writer.error("removing dependency", e)
