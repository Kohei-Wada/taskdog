.PHONY: help test test-core test-server test-ui test-all \
        install install-dev install-core install-server install-ui \
        install-ui-only install-server-only reinstall \
        tool-install-ui tool-install-server \
        clean lint format typecheck check

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "╔════════════════════════════════════════════════════════╗"
	@echo "║           Taskdog Makefile - Available Targets         ║"
	@echo "╚════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation:"
	@grep -E '^(install|reinstall|tool-install).*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🧪 Testing:"
	@grep -E '^test.*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "✨ Code Quality:"
	@grep -E '^(lint|format|typecheck|check).*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🧹 Cleanup:"
	@grep -E '^clean.*:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Installation Targets
# ============================================================================

install: ## Install all commands globally with uv tool (recommended)
	@echo "Installing taskdog-server globally..."
	cd packages/taskdog-server && uv tool install --force --reinstall .
	@echo "Installing taskdog globally..."
	cd packages/taskdog-ui && uv tool install --force --reinstall .
	@echo ""
	@echo "✓ All commands installed successfully!"
	@echo ""
	@echo "Available commands:"
	@echo "  - taskdog          (CLI/TUI)"
	@echo "  - taskdog-server   (API server)"
	@echo ""

install-dev: ## Install all packages with development dependencies (for development)
	@echo "Installing all packages with dev dependencies..."
	cd packages/taskdog-core && uv pip install -e ".[dev]"
	cd packages/taskdog-server && uv pip install -e ".[dev]"
	cd packages/taskdog-ui && uv pip install -e ".[dev]"
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""

install-core: ## Install taskdog-core package only (for development)
	@echo "Installing taskdog-core..."
	cd packages/taskdog-core && uv pip install -e .

install-server: install-core ## Install taskdog-server with pip (for development)
	@echo "Installing taskdog-server..."
	cd packages/taskdog-server && uv pip install -e .

install-ui: install-core ## Install taskdog-ui with pip (for development)
	@echo "Installing taskdog-ui..."
	cd packages/taskdog-ui && uv pip install -e .

install-local: install-core install-server install-ui ## Install all packages locally with pip (for development)
	@echo ""
	@echo "✓ All packages installed locally for development!"
	@echo ""

reinstall: clean install ## Clean and reinstall all commands globally
	@echo "✓ Reinstallation complete!"

# Uninstall
uninstall: ## Uninstall all commands
	@echo "Uninstalling taskdog commands..."
	-uv tool uninstall taskdog 2>/dev/null || true
	-uv tool uninstall taskdog-server 2>/dev/null || true
	@echo "✓ Uninstalled successfully!"

# ============================================================================
# Testing Targets
# ============================================================================

test: test-core test-ui ## Run all tests (core + ui)
	@echo ""
	@echo "✓ All tests passed!"
	@echo ""

test-all: test ## Run all tests (alias for test)

test-core: ## Run tests for taskdog-core only
	@echo "Running taskdog-core tests..."
	cd packages/taskdog-core && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

test-server: ## Run tests for taskdog-server only
	@echo "Running taskdog-server tests..."
	cd packages/taskdog-server && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

test-ui: ## Run tests for taskdog-ui only
	@echo "Running taskdog-ui tests..."
	cd packages/taskdog-ui && PYTHONPATH=src uv run python -m unittest discover -s tests/ -t .

# ============================================================================
# Code Quality Targets
# ============================================================================

lint: ## Check code with ruff linter
	@echo "Running ruff linter..."
	uv run ruff check packages/*/src/ packages/*/tests/

format: ## Format code with ruff and apply fixes
	@echo "Formatting code with ruff..."
	uv run ruff format packages/*/src/ packages/*/tests/
	uv run ruff check --fix packages/*/src/ packages/*/tests/

typecheck: ## Run mypy type checker on all packages
	@echo "Running mypy type checker..."
	uv run mypy packages/taskdog-core/src/
	uv run mypy packages/taskdog-server/src/
	uv run mypy packages/taskdog-ui/src/

check: lint typecheck ## Run all code quality checks (lint + typecheck)
	@echo ""
	@echo "✓ All code quality checks passed!"
	@echo ""

# ============================================================================
# Cleanup Targets
# ============================================================================

clean: ## Clean build artifacts and cache
	@echo "Cleaning build artifacts..."
	rm -rf packages/*/build/ packages/*/dist/ packages/*/src/*.egg-info/
	rm -rf packages/*/.ruff_cache/ packages/*/.mypy_cache/
	find packages -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	uv cache clean
	@echo "✓ Clean complete!"
