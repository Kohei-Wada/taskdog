.PHONY: test lint typecheck format

PACKAGE_NAME := taskdog_client
COV_THRESHOLD := 80
ROOT_DIR ?= ../..
CONFIG ?= $(ROOT_DIR)/pyproject.toml
PKG_PATH := packages/taskdog-client

test:
	PYTHONPATH=src uv run python -m pytest tests/ \
		--cov=$(PACKAGE_NAME) \
		--cov-report=term-missing:skip-covered \
		--cov-fail-under=$(COV_THRESHOLD)

lint:
	cd $(ROOT_DIR) && uv run ruff check --config pyproject.toml $(PKG_PATH)/src/ $(PKG_PATH)/tests/

format:
	cd $(ROOT_DIR) && uv run ruff format --config pyproject.toml $(PKG_PATH)/src/ $(PKG_PATH)/tests/
	cd $(ROOT_DIR) && uv run ruff check --fix --config pyproject.toml $(PKG_PATH)/src/ $(PKG_PATH)/tests/

typecheck:
	cd $(ROOT_DIR) && uv run mypy --config-file pyproject.toml $(PKG_PATH)/src/
