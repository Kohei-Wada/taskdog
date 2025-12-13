.PHONY: test lint typecheck format

PACKAGE_NAME := taskdog_core
COV_THRESHOLD := 90
CONFIG ?= ../../pyproject.toml

test:
	PYTHONPATH=src uv run python -m pytest tests/ \
		--cov=$(PACKAGE_NAME) \
		--cov-report=term-missing:skip-covered \
		--cov-fail-under=$(COV_THRESHOLD)

lint:
	uv run ruff check --config $(CONFIG) src/ tests/

format:
	uv run ruff format --config $(CONFIG) src/ tests/
	uv run ruff check --fix --config $(CONFIG) src/ tests/

typecheck:
	uv run mypy --config-file $(CONFIG) src/
