"""Dump command - Dump all tasks as JSON."""

import click
import json


@click.command(name="dump", help="Dump all tasks as JSON.")
@click.pass_context
def dump_command(ctx):
    """Dump all tasks as JSON."""
    task_query_service = ctx.obj["task_query_service"]

    try:
        tasks = task_query_service.get_all_tasks()
        tasks_json = json.dumps(
            [task.to_dict() for task in tasks], indent=4, ensure_ascii=False
        )
        print(tasks_json)
    except Exception as e:
        print(f"Error dumping tasks: {e}")
