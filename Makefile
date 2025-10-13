.PHONY: test install clean lint format typecheck check


test:
	PYTHONPATH=src uv run python -m unittest discover tests/

install:
	uv tool uninstall taskdog
	uv cache clean
	uv build
	uv tool install .

clean:
	rm -rf build/ dist/ src/*.egg-info/
	uv cache clean

# Linting and formatting
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck:
	PYTHONPATH=src uv run mypy src/

# Run all checks (lint + typecheck)
check: lint typecheck

completions: install
	_TASKDOG_COMPLETE=bash_source taskdog
