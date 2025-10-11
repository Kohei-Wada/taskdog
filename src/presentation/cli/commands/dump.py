"""Dump command - Dump all tasks as JSON."""

import click
import json
from application.queries.task_query_service import TaskQueryService


@click.command(name="dump", help="Dump all tasks as JSON.")
@click.pass_context
def dump_command(ctx):
    """Dump all tasks as JSON."""
    repository = ctx.obj["repository"]
    task_query_service = TaskQueryService(repository)

    try:
        tasks = task_query_service.get_all_tasks()
        tasks_json = json.dumps(
            [task.to_dict() for task in tasks], indent=4, ensure_ascii=False
        )
        print(tasks_json)
    except Exception as e:
        print(f"Error dumping tasks: {e}")
