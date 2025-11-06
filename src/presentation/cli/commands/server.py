"""Server command to run FastAPI application."""

import click


@click.command("server")
@click.option("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
@click.option("--port", default=8000, type=int, help="Port to bind (default: 8000)")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--workers", default=1, type=int, help="Number of worker processes (default: 1)")
def server_command(host: str, port: int, reload: bool, workers: int) -> None:
    """Start the Taskdog API server.

    This command starts a FastAPI server that provides a REST API
    for task management operations. The API supports all CLI/TUI
    functionality including CRUD operations, lifecycle management,
    dependencies, tags, statistics, and schedule optimization.

    Examples:
        taskdog server                        # Start server on default host:port
        taskdog server --host 0.0.0.0         # Listen on all interfaces
        taskdog server --port 3000            # Use custom port
        taskdog server --reload               # Enable auto-reload for dev
        taskdog server --workers 4            # Use 4 worker processes

    The API will be available at:
        - Root: http://{host}:{port}/
        - Docs: http://{host}:{port}/docs
        - Health: http://{host}:{port}/health
    """
    try:
        import uvicorn
    except ImportError:
        click.echo(
            "Error: uvicorn is not installed. Install it with: pip install 'taskdog[api]'",
            err=True,
        )
        raise click.Abort() from None

    click.echo(f"Starting Taskdog API server on {host}:{port}")
    click.echo(f"API documentation: http://{host}:{port}/docs")
    click.echo(f"Health check: http://{host}:{port}/health")
    click.echo()

    if reload and workers > 1:
        click.echo("Warning: --reload and --workers cannot be used together. Using --reload only.")
        workers = 1

    uvicorn.run(
        "presentation.api.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level="info",
    )
