# Concierge

A personal family concierge agent built with Claude Agent SDK (Python).

## Tech Stack

- Python 3.13
- uv (package manager)
- claude-agent-sdk (core dependency)
- pytest + pytest-asyncio (testing)

## How to Run

```bash
# Install dependencies
uv sync

# Set up your API key
cp .env.example .env
# Edit .env with your actual ANTHROPIC_API_KEY

# Run the concierge
uv run concierge "What time is it?"
# or
uv run python -m concierge "What time is it?"
```

## Running Tests

```bash
# Unit tests (fast, no API key needed)
uv run pytest tests/unit

# Integration tests (requires API key, hits real API)
uv run pytest -m integration
```

## Project Structure

- `src/concierge/` — Main package
  - `__main__.py` — CLI entry point
  - `agent.py` — Coordinator agent (routes requests to subagents/tools)
  - `agents/` — Subagent definitions (AgentDefinition instances)
  - `tools/` — Custom MCP tools (via @tool + create_sdk_mcp_server)
- `tests/` — Test suite
  - `unit/` — Fast tests, no external dependencies
  - `integration/` — Tests that hit the real Anthropic API

## Conventions

- Source code lives in `src/concierge/` (src layout)
- New subagents go in `src/concierge/agents/` as modules exporting an AgentDefinition
- New custom tools go in `src/concierge/tools/` using the @tool decorator
- Integration tests are marked with `@pytest.mark.integration`
