"""Tests for CLI error handling decorators."""

from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from taskdog.cli.error_handler import handle_command_errors, handle_task_errors
from taskdog_core.domain.exceptions.task_exceptions import (
    ServerConnectionError,
    TaskNotFoundException,
)


@pytest.fixture
def cli_context():
    ctx = MagicMock()
    ctx.console_writer = MagicMock()
    return ctx


def _run(command, cli_context):
    return CliRunner().invoke(command, [], obj=cli_context)


def test_handle_task_errors_exits_nonzero_on_task_not_found(cli_context):
    @click.command()
    @handle_task_errors("doing thing")
    @click.pass_context
    def cmd(ctx):
        raise TaskNotFoundException(1)

    result = _run(cmd, cli_context)

    assert result.exit_code != 0
    cli_context.console_writer.validation_error.assert_called_once()


def test_handle_task_errors_exits_nonzero_on_server_error(cli_context):
    @click.command()
    @handle_task_errors("doing thing")
    @click.pass_context
    def cmd(ctx):
        raise ServerConnectionError("http://localhost", RuntimeError("down"))

    result = _run(cmd, cli_context)

    assert result.exit_code != 0
    cli_context.console_writer.validation_error.assert_called_once()


def test_handle_task_errors_exits_nonzero_on_unexpected_error(cli_context):
    @click.command()
    @handle_task_errors("doing thing")
    @click.pass_context
    def cmd(ctx):
        raise RuntimeError("boom")

    result = _run(cmd, cli_context)

    assert result.exit_code != 0
    cli_context.console_writer.error.assert_called_once()


def test_handle_task_errors_exits_zero_on_success(cli_context):
    @click.command()
    @handle_task_errors("doing thing")
    @click.pass_context
    def cmd(ctx):
        ctx.obj.console_writer.print_success("ok")

    result = _run(cmd, cli_context)

    assert result.exit_code == 0


def test_handle_task_errors_passes_through_internal_exit(cli_context):
    """A deliberate ctx.exit(1) must not be re-reported as an unexpected error."""

    @click.command()
    @handle_task_errors("doing thing")
    @click.pass_context
    def cmd(ctx):
        ctx.exit(1)

    result = _run(cmd, cli_context)

    assert result.exit_code == 1
    cli_context.console_writer.error.assert_not_called()


def test_handle_command_errors_passes_through_internal_exit(cli_context):
    @click.command()
    @handle_command_errors("displaying")
    @click.pass_context
    def cmd(ctx):
        ctx.exit(1)

    result = _run(cmd, cli_context)

    assert result.exit_code == 1
    cli_context.console_writer.error.assert_not_called()


def test_handle_command_errors_exits_nonzero_on_server_error(cli_context):
    @click.command()
    @handle_command_errors("displaying")
    @click.pass_context
    def cmd(ctx):
        raise ServerConnectionError("http://localhost", RuntimeError("down"))

    result = _run(cmd, cli_context)

    assert result.exit_code != 0
    cli_context.console_writer.validation_error.assert_called_once()


def test_handle_command_errors_exits_nonzero_on_unexpected_error(cli_context):
    @click.command()
    @handle_command_errors("displaying")
    @click.pass_context
    def cmd(ctx):
        raise RuntimeError("boom")

    result = _run(cmd, cli_context)

    assert result.exit_code != 0
    cli_context.console_writer.error.assert_called_once()


def test_handle_command_errors_exits_zero_on_success(cli_context):
    @click.command()
    @handle_command_errors("displaying")
    @click.pass_context
    def cmd(ctx):
        ctx.obj.console_writer.print_success("ok")

    result = _run(cmd, cli_context)

    assert result.exit_code == 0
