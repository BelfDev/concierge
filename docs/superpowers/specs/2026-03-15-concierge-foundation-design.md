# Concierge Foundation — Design Spec

**Date:** 2026-03-15
**Status:** Approved
**Author:** Pedro Belfort + Claude

## Purpose

Build a minimal family concierge CLI agent using `claude-agent-sdk` (Python). This is both a learning vehicle for the Claude Certified Architect — Foundations exam and the foundation for a genuinely useful family assistant.

The goal of this first iteration is to prove out the core agentic patterns: coordinator agent, subagent spawning, and custom MCP tools. Real use cases (weekend planning, etc.) come in subsequent iterations.

## Context

Pedro is preparing for the Claude Certified Architect — Foundations Certification. The exam guide recommends: "Implement a complete agentic loop with tool calling, error handling, and session management. Practice spawning subagents and passing context between them."

This project exercises:
- **Domain 1 (27%):** Agentic loop, coordinator-subagent pattern, AgentDefinition, context passing
- **Domain 2 (18%):** Custom MCP tool design, `@tool` decorator, `create_sdk_mcp_server`
- **Domain 3 (20%):** CLAUDE.md configuration
- **Domain 5 (15%):** max_turns guard, error handling

## Tech Stack

- **Language:** Python 3.13
- **Package manager:** uv
- **Core dependency:** `claude-agent-sdk`
- **Other dependencies:** `python-dotenv`
- **Test framework:** `pytest`, `pytest-asyncio`
- **Interface:** CLI (`python -m concierge "your request"`)

## Project Structure

```
concierge/
├── .env                     # ANTHROPIC_API_KEY (gitignored)
├── .env.example             # Template showing required vars
├── .gitignore               # Python + .env + uv
├── .python-version          # 3.13
├── pyproject.toml           # uv project config
├── CLAUDE.md                # Claude Code project instructions
├── README.md                # Project overview, setup, usage
├── src/
│   └── concierge/
│       ├── __init__.py
│       ├── __main__.py      # CLI entry point
│       ├── agent.py         # Coordinator agent
│       ├── agents/
│       │   ├── __init__.py
│       │   └── echo.py      # Echo subagent (proof of concept)
│       └── tools/
│           ├── __init__.py
│           └── time_tool.py # Current time MCP tool
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_time_tool.py    # Unit tests for the time MCP tool
│   │   └── test_cli.py         # Unit tests for CLI arg parsing and env validation
│   └── integration/
│       ├── __init__.py
│       └── test_agent.py       # Integration tests for coordinator + subagent + tools
└── docs/
    └── superpowers/
        └── specs/
```

## Architecture

### Coordinator Agent (`agent.py`)

The coordinator is the main entry point. It uses `claude-agent-sdk`'s `query()` function with:

- **System prompt:** Instructs the agent to act as a family concierge that can delegate to specialized subagents
- **Allowed tools:** `Agent`, `WebSearch`, `WebFetch` (included so the coordinator can answer general knowledge questions without subagents), plus the custom time tool via MCP
- **Subagents:** Registered via the `agents` dict in `ClaudeAgentOptions`
- **Guard:** `max_turns=10` to prevent runaway loops

### Echo Subagent (`agents/echo.py`)

- Defined as an `AgentDefinition` with description, prompt, and scoped tools (`Read` only)
- Registered under key `"echo"` in the coordinator's agents dict
- Purpose: Prove subagent spawning works end-to-end

### Custom Time Tool (`tools/time_tool.py`)

- Uses `@tool` decorator from `claude-agent-sdk`
- Single tool: `get_current_time` — returns current date, time, day of week, and timezone
- Exposed via `create_sdk_mcp_server("time-tools", tools=[get_current_time])`
- Passed to coordinator via `mcp_servers={"time": server}`

### CLI Entry (`__main__.py`)

- Exports a `main()` function (referenced by the script entry point in `pyproject.toml`)
- Parses `sys.argv` for the user's prompt
- Loads `.env` via `python-dotenv`
- Validates `ANTHROPIC_API_KEY` is set before launching
- Runs the coordinator with `asyncio.run(run_concierge(prompt))`
- Prints `ResultMessage.result` to stdout

### Data Flow

```
User CLI input
  → Coordinator agent (query())
    → Decides: answer directly, use a tool, or spawn a subagent
      → Custom MCP tool (time) returns structured data
      → Subagent (echo) returns result via Agent tool
    → Coordinator synthesizes and responds
  → stdout
```

## Configuration & Infrastructure

### `pyproject.toml`
- uv project with `src` layout
- Dependencies: `claude-agent-sdk`, `python-dotenv`
- Dev dependencies: `pytest`, `pytest-asyncio`
- Script entry point: `concierge = "concierge.__main__:main"`
- Requires Python `>=3.13`

### Environment
- `.env` holds `ANTHROPIC_API_KEY` (gitignored)
- `.env.example` committed with placeholder

### `.gitignore`
- Python: `.venv/`, `__pycache__/`, `*.pyc`, `.egg-info/`, `dist/`
- Environment: `.env`
- IDE: `.idea/`, `.vscode/`

### `CLAUDE.md`
- Project description and purpose
- Tech stack
- How to run
- Project conventions (src layout, where agents/tools live)

## Error Handling

Minimal for v1:

- **Missing API key:** Check `os.environ` before launching, fail fast with clear instructions
- **SDK errors:** Catch `CLINotFoundError` and `CLIConnectionError` at the CLI level
- **Keyboard interrupt:** Graceful exit
- **Runaway loops:** `max_turns=10` on the coordinator

## Testing

### Unit Tests

**`tests/unit/test_time_tool.py`** — Tests the custom MCP tool in isolation:
- `get_current_time` returns a dict with expected keys (date, time, day_of_week, timezone)
- Returned date matches the current date
- Response format is valid (ISO 8601 date, etc.)

**`tests/unit/test_cli.py`** — Tests CLI plumbing without calling the SDK:
- Missing prompt argument prints usage and exits
- Missing `ANTHROPIC_API_KEY` exits with a clear error message
- Valid args are parsed correctly

### Integration Tests

**`tests/integration/test_agent.py`** — Tests the full agent pipeline (requires `ANTHROPIC_API_KEY`):
- Coordinator agent starts and returns a `ResultMessage`
- Coordinator can invoke the custom time tool and include time info in its response
- Coordinator can spawn the echo subagent and return its output

Integration tests are marked with `@pytest.mark.integration` so they can be run selectively (`uv run pytest -m integration`). They hit the real API and cost real tokens, so they should not run on every change.

### Fixtures (`tests/conftest.py`)
- `monkeypatch` for environment variables in unit tests
- Shared marker registration for `integration`

### Running Tests
- `uv run pytest tests/unit` — fast, no API key needed
- `uv run pytest -m integration` — requires API key, hits real API

## Deliberately Deferred

These are planned for future iterations, not v1:

- Real use cases (weekend planner, family calendar)
- Persistent state / session management
- Multiple specialized subagents (researcher, planner, etc.)
- Hooks (`PreToolUse`, `PostToolUse`) for data normalization and compliance
- Structured output schemas
- Streaming output
- API server interface

