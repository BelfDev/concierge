.PHONY: install test test-all test-integration run clean help

install: ## Install all dependencies
	uv sync

test: ## Run unit tests (fast, default)
	uv run pytest tests/unit -v

test-all: ## Run all tests (unit + integration)
	uv run pytest -v

test-integration: ## Run integration tests only (slow, requires Claude Code CLI)
	uv run pytest -m integration -v

run: ## Run the concierge (interactive, or one-shot with PROMPT="...")
ifdef PROMPT
	uv run concierge "$(PROMPT)"
else
	uv run concierge
endif

clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache .venv dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
