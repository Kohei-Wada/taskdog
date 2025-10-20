"""Add-dependency command - Add a task dependency."""

import click

from application.dto.manage_dependencies_input import AddDependencyInput
from application.use_cases.add_dependency import AddDependencyUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from presentation.cli.context import CliContext


@click.command(name="add-dependency", help="Add a dependency to a task.")
@click.argument("task_id", type=int)
@click.argument("depends_on_id", type=int)
@click.pass_context
def add_dependency_command(ctx, task_id, depends_on_id):
    """Add a dependency to a task.

    Usage:
        taskdog add-dependency <TASK_ID> <DEPENDS_ON_ID>

    Examples:
        taskdog add-dependency 5 3    # Task 5 depends on task 3
    """
    ctx_obj: CliContext = ctx.obj
    console_writer = ctx_obj.console_writer
    repository = ctx_obj.repository

    try:
        input_dto = AddDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        use_case = AddDependencyUseCase(repository)
        task = use_case.execute(input_dto)

        console_writer.success(
            f"Added dependency: Task {task_id} now depends on task {depends_on_id}"
        )
        console_writer.info(f"Task {task_id} dependencies: {task.depends_on}")

    except TaskNotFoundException as e:
        console_writer.validation_error(str(e))

    except TaskValidationError as e:
        console_writer.validation_error(str(e))

    except Exception as e:
        console_writer.error("adding dependency", e)
