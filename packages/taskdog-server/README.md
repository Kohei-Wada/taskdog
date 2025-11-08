# taskdog-server

FastAPI server for Taskdog task management system.

## Overview

This package provides a REST API for all Taskdog functionality including:

- Task CRUD operations
- Task lifecycle management (start, complete, pause, cancel, reopen)
- Task relationships (dependencies, tags)
- Time tracking and logging
- Schedule optimization
- Statistics and analytics

## Installation

```bash
pip install taskdog-server
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

Start the server:

```bash
taskdog-server
```

With custom options:

```bash
taskdog-server --host 0.0.0.0 --port 3000 --workers 4
```

Development mode with auto-reload:

```bash
taskdog-server --reload
```

## API Documentation

Once the server is running, visit:

- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Architecture

The server uses:

- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation with type hints
- **uvicorn**: ASGI server
- **taskdog-core**: Core business logic and infrastructure

## Dependencies

- `taskdog-core`: Core business logic
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation

## Testing

```bash
pytest tests/
```

## License

MIT
