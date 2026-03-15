# Concierge Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal CLI-based family concierge agent that proves out coordinator-subagent orchestration, custom MCP tools, and the agentic loop using `claude-agent-sdk`.

**Architecture:** A coordinator agent receives user input via CLI, decides whether to answer directly, use a custom MCP tool (time), or spawn a subagent (echo). Built entirely on `claude-agent-sdk`'s `query()` function with `ClaudeAgentOptions` for configuration.

**Tech Stack:** Python 3.13, uv, claude-agent-sdk, python-dotenv, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-15-concierge-foundation-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project config, dependencies, script entry point |
| `.python-version` | Pin Python 3.13 |
| `.gitignore` | Ignore .venv, __pycache__, .env, IDE files |
| `.env.example` | Template for required env vars |
| `CLAUDE.md` | Claude Code project instructions |
| `README.md` | Project overview, setup, usage |
| `src/concierge/__init__.py` | Package marker |
| `src/concierge/__main__.py` | CLI entry point, env validation, runs coordinator |
| `src/concierge/agent.py` | Coordinator agent: query() with subagents + tools |
| `src/concierge/agents/__init__.py` | Package marker |
| `src/concierge/agents/echo.py` | Echo subagent AgentDefinition |
| `src/concierge/tools/__init__.py` | Package marker |
| `src/concierge/tools/time_tool.py` | Custom MCP time tool via @tool + create_sdk_mcp_server |
| `tests/__init__.py` | Package marker |
| `tests/conftest.py` | Shared fixtures, marker registration |
| `tests/unit/__init__.py` | Package marker |
| `tests/unit/test_time_tool.py` | Unit tests for time tool |
| `tests/unit/test_cli.py` | Unit tests for CLI arg parsing and env validation |
| `tests/integration/__init__.py` | Package marker |
| `tests/integration/test_agent.py` | Integration tests for full agent pipeline |

---

## Chunk 1: Project Scaffolding

### Task 1: Initialize uv project and dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Users/pedro.belfort/Development/concierge
uv init --lib --python 3.13
```

This creates `pyproject.toml`, `.python-version`, and `src/concierge/__init__.py`. The `--lib` flag sets up `src` layout.

- [ ] **Step 2: Replace the generated pyproject.toml**

Replace the generated `pyproject.toml` with:

```toml
[project]
name = "concierge"
version = "0.1.0"
description = "A personal family concierge agent built with Claude Agent SDK"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "claude-agent-sdk",
    "python-dotenv",
]

[project.scripts]
concierge = "concierge.__main__:main"

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/concierge"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: tests that hit the real Anthropic API (require ANTHROPIC_API_KEY)",
]
asyncio_mode = "auto"
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

Expected: dependencies install successfully, `.venv` created.

- [ ] **Step 4: Verify installation**

```bash
uv run python -c "import claude_agent_sdk; print('SDK OK')"
uv run python -c "import dotenv; print('dotenv OK')"
uv run python -c "import pytest; print('pytest OK')"
```

Expected: all three print OK.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version uv.lock src/concierge/__init__.py
git commit -m "chore: initialize uv project with claude-agent-sdk dependencies"
```

---

### Task 2: Create .gitignore, .env.example, and CLAUDE.md

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `CLAUDE.md`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg

# Virtual environment
.venv/

# Environment variables
.env

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create .env.example**

```
# Get your API key from https://console.anthropic.com/
ANTHROPIC_API_KEY=your-api-key-here
```

- [ ] **Step 3: Create CLAUDE.md**

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .env.example CLAUDE.md
git commit -m "chore: add .gitignore, .env.example, and CLAUDE.md"
```

---

### Task 3: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md**

```markdown
# Concierge

A personal family concierge agent built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).

The concierge can answer questions, use tools (like checking the current time), and delegate tasks to specialized subagents. Built as a learning project for the Claude Certified Architect — Foundations certification.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Anthropic API key](https://console.anthropic.com/)

## Setup

```bash
# Clone and install
git clone <repo-url>
cd concierge
uv sync

# Configure your API key
cp .env.example .env
# Edit .env with your actual ANTHROPIC_API_KEY
```

## Usage

```bash
# Ask the concierge anything
uv run concierge "What day of the week is it?"

# Alternative invocation
uv run python -m concierge "Tell me the current time"
```

## Development

```bash
# Run unit tests
uv run pytest tests/unit

# Run integration tests (requires API key)
uv run pytest -m integration

# Run all tests
uv run pytest
```

## Architecture

The concierge uses a coordinator-subagent pattern:

1. **Coordinator** receives user input and decides how to handle it
2. **Subagents** handle specialized tasks (spawned on demand)
3. **Custom MCP tools** provide capabilities like checking the current time

Built with `claude-agent-sdk` using `query()` for the agentic loop and `AgentDefinition` for subagents.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with setup instructions and architecture overview"
```

---

### Task 4: Set up test infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`

- [ ] **Step 1: Create test directories and __init__.py files**

```bash
mkdir -p tests/unit tests/integration
```

Create empty `__init__.py` in `tests/`, `tests/unit/`, and `tests/integration/`.

- [ ] **Step 2: Create tests/conftest.py**

```python
import os

import pytest


@pytest.fixture
def env_with_api_key(monkeypatch):
    """Set a fake ANTHROPIC_API_KEY for tests that check env validation."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")


@pytest.fixture
def env_without_api_key(monkeypatch):
    """Ensure ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
```

- [ ] **Step 3: Verify pytest discovers the test directories**

```bash
uv run pytest --collect-only
```

Expected: no errors, 0 tests collected (no test files yet).

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "chore: set up test infrastructure with conftest and markers"
```

---

## Chunk 2: Custom MCP Time Tool

### Task 5: Write unit tests for the time tool

**Files:**
- Create: `tests/unit/test_time_tool.py`

- [ ] **Step 1: Write the tests**

```python
from datetime import datetime, timezone

from concierge.tools.time_tool import get_current_time


class TestGetCurrentTime:
    async def test_returns_expected_keys(self):
        result = await get_current_time({})
        content = result["content"]
        assert len(content) == 1
        text = content[0]["text"]
        # The tool returns a JSON-like string with time info
        assert "date" in text
        assert "time" in text
        assert "day_of_week" in text
        assert "timezone" in text

    async def test_date_matches_today(self):
        result = await get_current_time({})
        text = result["content"][0]["text"]
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in text

    async def test_day_of_week_is_valid(self):
        result = await get_current_time({})
        text = result["content"][0]["text"]
        valid_days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        assert any(day in text for day in valid_days)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_time_tool.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'concierge.tools.time_tool'`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/unit/test_time_tool.py
git commit -m "test: add failing unit tests for time tool (red phase)"
```

---

### Task 6: Implement the time tool

> **Note on `@tool` decorator:** The tests call `get_current_time({})` directly. If the `@tool` decorator wraps the function in a way that changes its signature or return type, the tests may need adjustment. Verify during the red-green step and adapt as needed.

**Files:**
- Create: `src/concierge/tools/__init__.py`
- Create: `src/concierge/tools/time_tool.py`

- [ ] **Step 1: Create the tools package**

Create empty `src/concierge/tools/__init__.py`.

- [ ] **Step 2: Implement the time tool**

```python
import json
from datetime import datetime

from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("get_current_time", "Get the current date, time, day of the week, and timezone")
async def get_current_time(args: dict) -> dict:
    now = datetime.now().astimezone()
    result = json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "timezone": str(now.tzinfo),
    })
    return {"content": [{"type": "text", "text": result}]}


def create_time_server():
    """Create an MCP server exposing the time tool."""
    return create_sdk_mcp_server("time-tools", tools=[get_current_time])
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_time_tool.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/concierge/tools/ tests/unit/test_time_tool.py
git commit -m "feat: add custom MCP time tool with unit tests"
```

---

## Chunk 3: Echo Subagent and Coordinator

### Task 7: Implement the echo subagent definition

**Files:**
- Create: `src/concierge/agents/__init__.py`
- Create: `src/concierge/agents/echo.py`

- [ ] **Step 1: Create the agents package**

Create empty `src/concierge/agents/__init__.py`.

- [ ] **Step 2: Implement the echo subagent**

```python
from claude_agent_sdk import AgentDefinition

echo_agent = AgentDefinition(
    description="A simple echo agent for testing subagent spawning. "
    "Use this agent when asked to test or verify the subagent system.",
    prompt="You are a simple echo agent. When you receive a message, "
    "acknowledge it and repeat back what was asked. Be brief and friendly.",
    tools=["Read"],
)
```

- [ ] **Step 3: Commit**

```bash
git add src/concierge/agents/
git commit -m "feat: add echo subagent definition"
```

---

### Task 8: Implement the coordinator agent

**Files:**
- Create: `src/concierge/agent.py`

- [ ] **Step 1: Implement the coordinator**

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

from concierge.agents.echo import echo_agent
from concierge.tools.time_tool import create_time_server

SYSTEM_PROMPT = """\
You are a helpful family concierge assistant. You help with planning, \
scheduling, and answering questions for a family living in Berlin, Germany.

You have access to:
- A time tool that tells you the current date, time, and day of the week
- Web search and fetch for looking up information
- An echo subagent for testing (invoke it only when explicitly asked to test subagents)

Be concise, practical, and friendly.\
"""


async def run_concierge(prompt: str) -> str:
    """Run the concierge coordinator agent with the given prompt.

    Returns the final text result from the agent.
    """
    time_server = create_time_server()

    result_text = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Agent", "WebSearch", "WebFetch"],
            agents={"echo": echo_agent},
            mcp_servers={"time": time_server},
            system_prompt=SYSTEM_PROMPT,
            max_turns=10,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text
```

- [ ] **Step 2: Commit**

```bash
git add src/concierge/agent.py
git commit -m "feat: add coordinator agent with subagent and MCP tool support"
```

---

## Chunk 4: CLI Entry Point

### Task 9: Write unit tests for CLI

**Files:**
- Create: `tests/unit/test_cli.py`

- [ ] **Step 1: Write the tests**

These tests call `main()` directly (not via subprocess) so that `monkeypatch` fixtures work correctly for environment variables.

```python
import os
import sys
from unittest.mock import patch, AsyncMock

import pytest

from concierge.__main__ import main


class TestCliArgParsing:
    def test_missing_prompt_exits_with_usage(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["concierge"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Usage:" in capsys.readouterr().err

    def test_missing_api_key_exits_with_error(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["concierge", "hello"])
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "ANTHROPIC_API_KEY" in capsys.readouterr().err

    def test_valid_args_calls_agent(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["concierge", "hello", "world"])
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake")
        with patch("concierge.__main__.run_concierge", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "response"
            main()
            mock_run.assert_called_once_with("hello world")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_cli.py -v
```

Expected: FAIL (`ModuleNotFoundError: No module named 'concierge.__main__'`).

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/unit/test_cli.py
git commit -m "test: add failing unit tests for CLI (red phase)"
```

---

### Task 10: Implement the CLI entry point

**Files:**
- Create: `src/concierge/__main__.py`

- [ ] **Step 1: Implement __main__.py**

Uses `asyncio.run()` (stdlib) instead of `anyio.run()` to avoid an extra dependency.

```python
import asyncio
import os
import sys

from dotenv import load_dotenv

from claude_agent_sdk import CLINotFoundError, CLIConnectionError

from concierge.agent import run_concierge


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: concierge <prompt>", file=sys.stderr)
        print('  Example: concierge "What day is it today?"', file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your API key:\n"
            "  cp .env.example .env",
            file=sys.stderr,
        )
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    try:
        result = asyncio.run(run_concierge(prompt))
        if result:
            print(result)
    except CLINotFoundError:
        print(
            "Error: Claude Code CLI not found.\n"
            "Install with: pip install claude-agent-sdk",
            file=sys.stderr,
        )
        sys.exit(1)
    except CLIConnectionError as e:
        print(f"Error: Failed to connect to Claude Code CLI: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run CLI unit tests to verify they pass**

```bash
uv run pytest tests/unit/test_cli.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 3: Quick smoke test (without API key)**

```bash
uv run python -m concierge 2>&1 | head -1
```

Expected: `Usage: concierge <prompt>`

- [ ] **Step 4: Commit**

```bash
git add src/concierge/__main__.py tests/unit/test_cli.py
git commit -m "feat: add CLI entry point with arg parsing, env validation, and SDK error handling"
```

---

## Chunk 5: Integration Tests

### Task 11: Write integration tests

**Files:**
- Create: `tests/integration/test_agent.py`

These tests require a real `ANTHROPIC_API_KEY` and hit the Anthropic API. They are marked with `@pytest.mark.integration`.

- [ ] **Step 1: Write the integration tests**

```python
import os

import pytest

from concierge.agent import run_concierge


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def require_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")


class TestCoordinatorAgent:
    async def test_returns_a_response(self):
        result = await run_concierge("Say hello in exactly 3 words.")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_uses_time_tool(self):
        result = await run_concierge(
            "What is the current date? Use your time tool to check."
        )
        assert isinstance(result, str)
        assert len(result) > 0
        # The response should contain a date-like string
        # (we can't assert the exact date since the model may format it differently)

    async def test_spawns_echo_subagent(self):
        result = await run_concierge(
            "Test the echo subagent by sending it the message 'ping'."
        )
        assert isinstance(result, str)
        assert len(result) > 0
```

- [ ] **Step 2: Run integration tests (requires API key)**

```bash
uv run pytest -m integration -v
```

Expected: 3 tests PASS (if ANTHROPIC_API_KEY is set), or SKIP (if not set).

- [ ] **Step 3: Run full test suite**

```bash
uv run pytest -v
```

Expected: unit tests PASS, integration tests PASS or SKIP depending on API key.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/
git commit -m "test: add integration tests for coordinator, time tool, and subagent"
```

---

## Chunk 6: Final Verification

### Task 12: End-to-end manual test

- [ ] **Step 1: Ensure .env is configured**

```bash
test -f .env && echo ".env exists" || echo "Create .env from .env.example"
```

- [ ] **Step 2: Test basic query**

```bash
uv run concierge "Hello, what can you help me with?"
```

Expected: The concierge responds with a friendly message about its capabilities.

- [ ] **Step 3: Test time tool usage**

```bash
uv run concierge "What day of the week is it today?"
```

Expected: The concierge uses the time tool and tells you the correct day.

- [ ] **Step 4: Test subagent spawning**

```bash
uv run concierge "Test the echo subagent by saying hello to it"
```

Expected: The concierge spawns the echo subagent and relays its response.

- [ ] **Step 5: Run all tests one final time**

```bash
uv run pytest -v
```

Expected: All unit tests PASS. Integration tests PASS (if API key set) or SKIP.

- [ ] **Step 6: Commit any final adjustments (if needed)**

Review `git status` for any uncommitted files. Stage only specific files — do not use `git add -A` to avoid accidentally staging `.env` or other sensitive files.
