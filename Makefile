.PHONY: help test install clean lint format typecheck check completions

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

test: ## Run all tests
	uv run python -m unittest discover tests/

install: ## Install taskdog CLI tool
	uv tool uninstall taskdog
	uv cache clean
	uv build
	uv tool install .

clean: ## Clean build artifacts and cache
	rm -rf build/ dist/ src/*.egg-info/
	uv cache clean

lint: ## Check code with ruff linter
	uv run ruff check src/ tests/

format: ## Format code with ruff and apply fixes
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck: ## Run mypy type checker
	uv run mypy src/

check: lint typecheck ## Run all code quality checks (lint + typecheck)

completions: install ## Generate shell completions (requires installation)
	_TASKDOG_COMPLETE=bash_source taskdog
