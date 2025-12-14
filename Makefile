.PHONY: help test test-core test-server test-ui test-client test-mcp test-all \
        install install-dev install-core install-server install-ui install-client install-mcp \
        install-ui-only install-server-only reinstall \
        tool-install-ui tool-install-server check-deps \
        clean lint format typecheck check \
        lint-core lint-client lint-server lint-ui lint-mcp \
        typecheck-core typecheck-client typecheck-server typecheck-ui typecheck-mcp

.DEFAULT_GOAL := help

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
endif

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

check-deps: ## Check if required tools are installed
	@echo "Checking required dependencies..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ Error: uv is not installed. Install it from https://github.com/astral-sh/uv"; exit 1; }
	@echo "✓ uv is installed"
ifeq ($(PLATFORM),linux)
	@command -v systemctl >/dev/null 2>&1 || { echo "❌ Error: systemctl is not installed"; exit 1; }
	@echo "✓ systemctl is installed"
else ifeq ($(PLATFORM),macos)
	@command -v launchctl >/dev/null 2>&1 || { echo "❌ Error: launchctl is not installed"; exit 1; }
	@echo "✓ launchctl is installed"
endif
	@echo "✓ All dependencies are installed"
	@echo ""

install: check-deps ## Install all commands globally with uv tool (recommended)
	@echo "Installing taskdog-server globally..."
	cd packages/taskdog-server && uv tool install --force --reinstall .
	@echo "Installing taskdog globally..."
	cd packages/taskdog-ui && uv tool install --force --reinstall .
	@echo "Installing taskdog-mcp globally..."
	cd packages/taskdog-mcp && uv tool install --force --reinstall .
	@echo ""
ifeq ($(PLATFORM),linux)
	@echo "Setting up systemd user service..."
	@mkdir -p ~/.config/systemd/user
	@cp contrib/systemd/taskdog-server.service ~/.config/systemd/user/
	@systemctl --user daemon-reload
	@systemctl --user enable taskdog-server.service
	@echo ""
	@echo "✓ All commands installed successfully!"
	@echo ""
	@echo "Available commands:"
	@echo "  - taskdog          (CLI/TUI)"
	@echo "  - taskdog-server   (API server)"
	@echo "  - taskdog-mcp      (MCP server for Claude Desktop)"
	@echo ""
	@echo "Systemd service installed and enabled:"
	@echo "  - Start:  systemctl --user start taskdog-server"
	@echo "  - Status: systemctl --user status taskdog-server"
	@echo "  - Logs:   journalctl --user -u taskdog-server -f"
	@echo ""
	@echo "See contrib/README.md for more details."
	@echo ""
else ifeq ($(PLATFORM),macos)
	@echo "Setting up launchd service..."
	@mkdir -p ~/Library/LaunchAgents
	@mkdir -p ~/Library/Logs
	@sed 's|%USER%|$(USER)|g' contrib/launchd/taskdog-server.plist > ~/Library/LaunchAgents/com.github.kohei-wada.taskdog-server.plist
	@launchctl load ~/Library/LaunchAgents/com.github.kohei-wada.taskdog-server.plist 2>/dev/null || true
	@echo ""
	@echo "✓ All commands installed successfully!"
	@echo ""
	@echo "Available commands:"
	@echo "  - taskdog          (CLI/TUI)"
	@echo "  - taskdog-server   (API server)"
	@echo "  - taskdog-mcp      (MCP server for Claude Desktop)"
	@echo ""
	@echo "Launchd service installed and enabled:"
	@echo "  - Start:  launchctl start com.github.kohei-wada.taskdog-server"
	@echo "  - Stop:   launchctl stop com.github.kohei-wada.taskdog-server"
	@echo "  - Status: launchctl list | grep taskdog-server"
	@echo "  - Logs:   tail -f ~/Library/Logs/taskdog-server.log"
	@echo ""
else
	@echo "✓ All commands installed successfully!"
	@echo ""
	@echo "Available commands:"
	@echo "  - taskdog          (CLI/TUI)"
	@echo "  - taskdog-server   (API server)"
	@echo "  - taskdog-mcp      (MCP server for Claude Desktop)"
	@echo ""
	@echo "Note: Automatic service management not supported on this platform."
	@echo "Start the server manually: taskdog-server --host 127.0.0.1 --port 8000"
	@echo ""
endif

install-dev: ## Install all packages with development dependencies (for development)
	@echo "Installing all packages with dev dependencies..."
	cd packages/taskdog-core && uv pip install -e ".[dev]"
	cd packages/taskdog-client && uv pip install -e ".[dev]"
	cd packages/taskdog-server && uv pip install -e ".[dev]"
	cd packages/taskdog-ui && uv pip install -e ".[dev]"
	cd packages/taskdog-mcp && uv pip install -e ".[dev]"
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""

install-core: ## Install taskdog-core package only (for development)
	@echo "Installing taskdog-core..."
	cd packages/taskdog-core && uv pip install -e .

install-server: install-core ## Install taskdog-server with pip (for development)
	@echo "Installing taskdog-server..."
	cd packages/taskdog-server && uv pip install -e .

install-client: install-core ## Install taskdog-client with pip (for development)
	@echo "Installing taskdog-client..."
	cd packages/taskdog-client && uv pip install -e .

install-ui: install-client ## Install taskdog-ui with pip (for development)
	@echo "Installing taskdog-ui..."
	cd packages/taskdog-ui && uv pip install -e .

install-mcp: install-client ## Install taskdog-mcp with pip (for development)
	@echo "Installing taskdog-mcp..."
	cd packages/taskdog-mcp && uv pip install -e .

install-local: install-core install-client install-server install-ui install-mcp ## Install all packages locally with pip (for development)
	@echo ""
	@echo "✓ All packages installed locally for development!"
	@echo ""

reinstall: clean install ## Clean and reinstall all commands globally
	@echo "✓ Reinstallation complete!"

# Uninstall
uninstall: ## Uninstall all commands
ifeq ($(PLATFORM),linux)
	@echo "Stopping and disabling systemd service..."
	-systemctl --user stop taskdog-server.service 2>/dev/null || true
	-systemctl --user disable taskdog-server.service 2>/dev/null || true
	-rm -f ~/.config/systemd/user/taskdog-server.service
	-systemctl --user daemon-reload
else ifeq ($(PLATFORM),macos)
	@echo "Stopping and unloading launchd service..."
	-launchctl unload ~/Library/LaunchAgents/com.github.kohei-wada.taskdog-server.plist 2>/dev/null || true
	-rm -f ~/Library/LaunchAgents/com.github.kohei-wada.taskdog-server.plist
endif
	@echo "Uninstalling taskdog commands..."
	-uv tool uninstall taskdog 2>/dev/null || true
	-uv tool uninstall taskdog-server 2>/dev/null || true
	-uv tool uninstall taskdog-mcp 2>/dev/null || true
	@echo "✓ Uninstalled successfully!"

# ============================================================================
# Testing Targets (recursive)
# ============================================================================

PACKAGES := taskdog-core taskdog-client taskdog-server taskdog-ui taskdog-mcp
ROOT_DIR := $(shell pwd)
CONFIG := $(ROOT_DIR)/pyproject.toml

test: $(addprefix test-,$(PACKAGES)) ## Run all tests with coverage
	@echo ""
	@echo "✓ All tests passed!"
	@echo ""

test-all: test ## Run all tests (alias for test)

test-%: ## Run tests for a specific package (e.g., make test-taskdog-core)
	@echo "Running $* tests..."
	$(MAKE) -C packages/$* test

# Convenience aliases for testing
test-core: test-taskdog-core ## Run taskdog-core tests
test-client: test-taskdog-client ## Run taskdog-client tests
test-server: test-taskdog-server ## Run taskdog-server tests
test-ui: test-taskdog-ui ## Run taskdog-ui tests
test-mcp: test-taskdog-mcp ## Run taskdog-mcp tests

# ============================================================================
# Code Quality Targets (recursive)
# ============================================================================

lint: $(addprefix lint-,$(PACKAGES)) ## Check code with ruff linter
	@echo ""
	@echo "✓ Lint passed!"
	@echo ""

lint-%: ## Lint a specific package (e.g., make lint-taskdog-core)
	@echo "Linting $*..."
	$(MAKE) -C packages/$* lint ROOT_DIR=$(ROOT_DIR)

# Convenience aliases for linting
lint-core: lint-taskdog-core ## Lint taskdog-core
lint-client: lint-taskdog-client ## Lint taskdog-client
lint-server: lint-taskdog-server ## Lint taskdog-server
lint-ui: lint-taskdog-ui ## Lint taskdog-ui
lint-mcp: lint-taskdog-mcp ## Lint taskdog-mcp

format: $(addprefix format-,$(PACKAGES)) ## Format code with ruff and apply fixes
	@echo ""
	@echo "✓ Format complete!"
	@echo ""

format-%: ## Format a specific package (e.g., make format-taskdog-core)
	@echo "Formatting $*..."
	$(MAKE) -C packages/$* format ROOT_DIR=$(ROOT_DIR)

typecheck: $(addprefix typecheck-,$(PACKAGES)) ## Run mypy type checker on all packages
	@echo ""
	@echo "✓ Type check passed!"
	@echo ""

typecheck-%: ## Type check a specific package (e.g., make typecheck-taskdog-core)
	@echo "Type checking $*..."
	$(MAKE) -C packages/$* typecheck ROOT_DIR=$(ROOT_DIR)

# Convenience aliases for type checking
typecheck-core: typecheck-taskdog-core ## Type check taskdog-core
typecheck-client: typecheck-taskdog-client ## Type check taskdog-client
typecheck-server: typecheck-taskdog-server ## Type check taskdog-server
typecheck-ui: typecheck-taskdog-ui ## Type check taskdog-ui
typecheck-mcp: typecheck-taskdog-mcp ## Type check taskdog-mcp

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
ifeq ($(PLATFORM),linux)
	@echo "Stopping systemd service..."
	-systemctl --user stop taskdog-server.service 2>/dev/null || true
else ifeq ($(PLATFORM),macos)
	@echo "Stopping launchd service..."
	-launchctl stop com.github.kohei-wada.taskdog-server 2>/dev/null || true
endif
	@echo "✓ Clean complete!"
