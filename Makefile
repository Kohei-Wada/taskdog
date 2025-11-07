.PHONY: help test test-core test-server test-ui install install-core install-server install-ui install-all clean lint format typecheck check

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Testing
test: ## Run all tests (all packages)
	@echo "Running tests for taskdog-core..."
	cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .
	@echo "Running tests for taskdog-ui..."
	cd packages/taskdog-ui && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

test-core: ## Run tests for taskdog-core only
	cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

test-server: ## Run tests for taskdog-server only
	cd packages/taskdog-server && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

test-ui: ## Run tests for taskdog-ui only
	cd packages/taskdog-ui && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

# Installation
install-core: ## Install taskdog-core package
	cd packages/taskdog-core && uv pip install -e .

install-server: install-core ## Install taskdog-server (includes core)
	cd packages/taskdog-server && uv pip install -e .

install-ui: install-core ## Install taskdog-ui (includes core)
	cd packages/taskdog-ui && uv pip install -e .

install-all: install-core install-server install-ui ## Install all packages

install: install-ui ## Install taskdog UI (default, for backward compatibility)

# Tool installation (global)
tool-install-ui: ## Install taskdog CLI tool globally
	cd packages/taskdog-ui && uv tool install .

tool-install-server: ## Install taskdog-server CLI tool globally
	cd packages/taskdog-server && uv tool install .

# Clean
clean: ## Clean build artifacts and cache
	rm -rf packages/*/build/ packages/*/dist/ packages/*/src/*.egg-info/
	uv cache clean

# Code Quality
lint: ## Check code with ruff linter
	uv run ruff check packages/*/src/ packages/*/tests/

format: ## Format code with ruff and apply fixes
	uv run ruff format packages/*/src/ packages/*/tests/
	uv run ruff check --fix packages/*/src/ packages/*/tests/

typecheck: ## Run mypy type checker
	uv run mypy packages/taskdog-core/src/
	uv run mypy packages/taskdog-server/src/
	uv run mypy packages/taskdog-ui/src/

check: lint typecheck ## Run all code quality checks (lint + typecheck)
