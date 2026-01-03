"""Common CLI option decorators for reuse across commands."""

from collections.abc import Callable
from functools import wraps
from typing import Any

import click


def filter_options() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add common filter options (--all, --status) to a command.

    Usage:
        @click.command()
        @filter_options()
        def my_command(ctx, all, status, ...):
            pass
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @click.option(
            "--status",
            type=click.Choice(
                ["pending", "in_progress", "completed", "canceled"],
                case_sensitive=False,
            ),
            default=None,
            help="Filter tasks by status (overrides --all). Note: archived tasks are controlled by the --all flag, not --status.",
        )
        @click.option(
            "--all",
            "-a",
            is_flag=True,
            help="Show all tasks including completed, canceled, and archived",
        )
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        return wrapper

    return decorator


def sort_options(
    default_sort: str = "id",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add common sort options (--sort, --reverse) to a command.

    Args:
        default_sort: Default field to sort by (default: "id")

    Usage:
        @click.command()
        @sort_options(default_sort="deadline")
        def my_command(ctx, sort, reverse, ...):
            pass
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @click.option(
            "--reverse",
            "-r",
            is_flag=True,
            help="Reverse sort order",
        )
        @click.option(
            "--sort",
            type=click.Choice(
                ["id", "priority", "deadline", "name", "status", "planned_start"]
            ),
            default=default_sort,
            help=f"Sort tasks by specified field (default: {default_sort})",
        )
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        return wrapper

    return decorator


def date_range_options() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add common date range options (--start-date, --end-date) to a command.

    Usage:
        @click.command()
        @date_range_options()
        def my_command(ctx, start_date, end_date, ...):
            pass
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @click.option(
            "--end-date",
            "-e",
            type=click.DateTime(),
            help="End date for filtering (YYYY-MM-DD). "
            "Shows tasks with any date field <= end date.",
        )
        @click.option(
            "--start-date",
            "-s",
            type=click.DateTime(),
            help="Start date for filtering (YYYY-MM-DD). "
            "Shows tasks with any date field >= start date.",
        )
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        return wrapper

    return decorator
