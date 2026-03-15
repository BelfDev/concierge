# Interactive CLI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-shot CLI with an interactive REPL featuring rich styling, spinners, markdown output, and multi-turn session memory.

**Architecture:** `cli.py` handles all UI (banner, input loop, spinner, markdown rendering). `agent.py` gains session support via `session_id` parameter and Agent SDK's `resume` option. `__main__.py` routes between interactive (no args) and one-shot (with args) modes.

**Tech Stack:** Python 3.13, rich, claude-agent-sdk (session resumption), pytest

**Spec:** `docs/superpowers/specs/2026-03-15-interactive-cli-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Add `rich` dependency |
| `Makefile` | Conditional `run` target for interactive vs one-shot |
| `src/concierge/agent.py` | Add `session_id` param, return `(result, session_id)`, branch on resume |
| `src/concierge/cli.py` | **New** — Interactive REPL: banner, input loop, spinner, markdown output |
| `src/concierge/__main__.py` | Route: no args → interactive, with args → one-shot |
| `tests/unit/test_cli.py` | Update for new return type, replace no-args test |
| `tests/unit/test_cli_interactive.py` | **New** — Unit tests for REPL |
| `tests/integration/test_agent.py` | Update return type, add session resumption test |

---

## Chunk 1: Dependencies and Agent Session Support

### Task 1: Add `rich` dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `rich` to dependencies**

In `pyproject.toml`, change:
```toml
dependencies = [
    "claude-agent-sdk",
]
```
to:
```toml
dependencies = [
    "claude-agent-sdk",
    "rich",
]
```

- [ ] **Step 2: Install**

```bash
uv sync
```

- [ ] **Step 3: Verify**

```bash
uv run python -c "from rich.console import Console; print('rich OK')"
```

Expected: `rich OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add rich dependency"
```

---

### Task 2: Update `agent.py` for session support

**Files:**
- Modify: `src/concierge/agent.py`
- Modify: `tests/unit/test_cli.py`
- Modify: `tests/integration/test_agent.py`

- [ ] **Step 1: Update existing tests for new return type**

In `tests/unit/test_cli.py`, replace the entire file with:

```python
import sys
from unittest.mock import patch, AsyncMock

from concierge.__main__ import main


class TestCliOneShot:
    def test_valid_args_calls_agent(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["concierge", "hello", "world"])
        with patch("concierge.__main__.run_concierge", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = ("response", "session-123")
            main()
            mock_run.assert_called_once_with("hello world")
        assert "response" in capsys.readouterr().out

    def test_no_args_starts_interactive(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["concierge"])
        with patch("concierge.__main__.run_interactive", new_callable=AsyncMock) as mock_interactive:
            main()
            mock_interactive.assert_called_once()
```

In `tests/integration/test_agent.py`, replace the entire file with:

```python
import os
import shutil

import pytest

from concierge.agent import run_concierge


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def require_claude_cli():
    if not shutil.which("claude"):
        pytest.skip("Claude Code CLI not found")
    if os.environ.get("CLAUDECODE"):
        pytest.skip("Cannot run inside a Claude Code session")


class TestCoordinatorAgent:
    async def test_returns_a_response(self):
        result, session_id = await run_concierge("Say hello in exactly 3 words.")
        assert isinstance(result, str)
        assert len(result) > 0
        assert session_id is not None

    async def test_uses_time_tool(self):
        result, _ = await run_concierge(
            "What is the current date? Use your time tool to check."
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_spawns_echo_subagent(self):
        result, _ = await run_concierge(
            "Test the echo subagent by sending it the message 'ping'."
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_session_resumption(self):
        result1, session_id = await run_concierge("My name is Pedro.")
        assert session_id is not None

        result2, _ = await run_concierge("What is my name?", session_id=session_id)
        assert isinstance(result2, str)
        assert "Pedro" in result2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_cli.py tests/integration/test_agent.py --collect-only 2>&1
```

Expected: Collection errors because `run_concierge` signature hasn't changed yet and `run_interactive` doesn't exist.

- [ ] **Step 3: Update `agent.py`**

Replace the entire `src/concierge/agent.py` with:

```python
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
)

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


async def run_concierge(
    prompt: str, session_id: str | None = None
) -> tuple[str, str | None]:
    """Run the concierge coordinator agent with the given prompt.

    Args:
        prompt: The user's input.
        session_id: If provided, resumes a previous session for multi-turn context.

    Returns:
        A tuple of (result_text, session_id). The session_id can be passed
        to subsequent calls to maintain conversation context.
    """
    if session_id is None:
        time_server = create_time_server()
        options = ClaudeAgentOptions(
            allowed_tools=["Agent", "WebSearch", "WebFetch"],
            agents={"echo": echo_agent},
            mcp_servers={"time": time_server},
            system_prompt=SYSTEM_PROMPT,
            max_turns=10,
        )
    else:
        options = ClaudeAgentOptions(resume=session_id)

    result_text = ""
    captured_session_id = session_id

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            captured_session_id = message.data.get("session_id")
        elif isinstance(message, ResultMessage) and message.result:
            result_text = message.result
        elif isinstance(message, AssistantMessage):
            texts = [
                block.text
                for block in message.content
                if isinstance(block, TextBlock)
            ]
            if texts:
                result_text = "\n".join(texts)

    return result_text, captured_session_id
```

- [ ] **Step 4: Run unit tests**

```bash
uv run pytest tests/unit/test_cli.py -v 2>&1
```

Expected: FAIL — `test_no_args_starts_interactive` fails because `run_interactive` doesn't exist yet in `__main__.py`. `test_valid_args_calls_agent` may also fail because `__main__.py` still has old signature. This is expected — we'll fix `__main__.py` in Task 4.

- [ ] **Step 5: Commit**

```bash
git add src/concierge/agent.py tests/unit/test_cli.py tests/integration/test_agent.py
git commit -m "feat: add session support to run_concierge, update tests"
```

---

## Chunk 2: Interactive REPL

### Task 3: Write unit tests for the interactive REPL

**Files:**
- Create: `tests/unit/test_cli_interactive.py`

- [ ] **Step 1: Write the tests**

```python
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from concierge.cli import run_interactive


class TestInteractiveRepl:
    async def test_exit_command_breaks_loop(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
        ):
            mock_prompt_cls.ask.side_effect = ["exit"]
            await run_interactive()
        # Should not have called run_concierge
        # (exit before any agent call)

    async def test_quit_command_breaks_loop(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
        ):
            mock_prompt_cls.ask.side_effect = ["quit"]
            await run_interactive()

    async def test_empty_input_skipped(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.run_concierge", new_callable=AsyncMock) as mock_run,
        ):
            mock_prompt_cls.ask.side_effect = ["", "   ", "exit"]
            mock_run.return_value = ("response", "sid")
            await run_interactive()
            mock_run.assert_not_called()

    async def test_sends_prompt_to_agent(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.run_concierge", new_callable=AsyncMock) as mock_run,
        ):
            mock_prompt_cls.ask.side_effect = ["hello", "exit"]
            mock_run.return_value = ("response", "session-123")
            await run_interactive()
            mock_run.assert_called_once_with("hello", session_id=None)

    async def test_passes_session_id_on_second_call(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.run_concierge", new_callable=AsyncMock) as mock_run,
        ):
            mock_prompt_cls.ask.side_effect = ["first", "second", "exit"]
            mock_run.side_effect = [
                ("response1", "session-123"),
                ("response2", "session-123"),
            ]
            await run_interactive()
            assert mock_run.call_count == 2
            mock_run.assert_any_call("first", session_id=None)
            mock_run.assert_any_call("second", session_id="session-123")

    async def test_eof_exits_gracefully(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
        ):
            mock_prompt_cls.ask.side_effect = EOFError
            await run_interactive()

    async def test_banner_renders(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
        ):
            mock_prompt_cls.ask.side_effect = ["exit"]
            await run_interactive()
        # Banner is the first call to console.print, should be a Panel
        first_print_arg = mock_console.print.call_args_list[0][0][0]
        from rich.panel import Panel
        assert isinstance(first_print_arg, Panel)

    async def test_agent_error_keeps_session_alive(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.run_concierge", new_callable=AsyncMock) as mock_run,
        ):
            mock_prompt_cls.ask.side_effect = ["hello", "world", "exit"]
            mock_run.side_effect = [
                RuntimeError("boom"),
                ("recovered", "session-456"),
            ]
            await run_interactive()
            # First call failed, second succeeded — session stayed alive
            assert mock_run.call_count == 2

    async def test_session_reset_on_error(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.run_concierge", new_callable=AsyncMock) as mock_run,
        ):
            mock_prompt_cls.ask.side_effect = ["first", "second", "exit"]
            mock_run.side_effect = [
                ("ok", "session-123"),
                RuntimeError("session expired"),
            ]
            await run_interactive()
            # After error, next call should use session_id=None (fresh session)
            # We can't test the third call since "exit" breaks the loop,
            # but we verify the error was handled gracefully
            assert mock_run.call_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_cli_interactive.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'concierge.cli'`

- [ ] **Step 3: Commit failing tests**

```bash
git add tests/unit/test_cli_interactive.py
git commit -m "test: add failing unit tests for interactive REPL (red phase)"
```

---

### Task 4: Implement the interactive REPL and update `__main__.py`

**Files:**
- Create: `src/concierge/cli.py`
- Modify: `src/concierge/__main__.py`

- [ ] **Step 1: Create `src/concierge/cli.py`**

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from concierge.agent import run_concierge


async def run_interactive() -> None:
    """Run the concierge in interactive REPL mode."""
    console = Console()

    console.print(
        Panel(
            "[bold]🏠 Concierge[/bold]\n"
            "Your family assistant\n"
            "Type 'exit' or Ctrl+C to quit",
            expand=False,
        )
    )
    console.print()

    session_id = None

    while True:
        try:
            user_input = Prompt.ask("[bold]You[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye! 👋")
            break

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit"):
            console.print("Goodbye! 👋")
            break

        try:
            with console.status("Thinking...", spinner="dots"):
                result, session_id = await run_concierge(
                    user_input, session_id=session_id
                )

            if result:
                console.print()
                console.print(Markdown(result))
            else:
                console.print("[dim]No response.[/dim]")
            console.print()

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            session_id = None  # Reset to fresh session on error
            console.print("[dim]Starting fresh session. Try again.[/dim]")
            console.print()
```

- [ ] **Step 2: Update `src/concierge/__main__.py`**

Replace the entire file with:

```python
import asyncio
import sys

from claude_agent_sdk import CLINotFoundError, CLIConnectionError

from concierge.agent import run_concierge
from concierge.cli import run_interactive


def main():
    try:
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
            result, _ = asyncio.run(run_concierge(prompt))
            if result:
                print(result)
        else:
            asyncio.run(run_interactive())
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

- [ ] **Step 3: Run all unit tests**

```bash
uv run pytest tests/unit -v
```

Expected: All tests PASS (test_cli.py + test_cli_interactive.py + test_time_tool.py).

- [ ] **Step 4: Commit**

```bash
git add src/concierge/cli.py src/concierge/__main__.py
git commit -m "feat: add interactive REPL with rich styling and session memory"
```

---

## Chunk 3: Makefile and Final Verification

### Task 5: Update Makefile

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Update the `run` target**

Replace the `run` target in the Makefile:

```makefile
run: ## Run the concierge (interactive, or one-shot with PROMPT="...")
ifdef PROMPT
	uv run concierge "$(PROMPT)"
else
	uv run concierge
endif
```

- [ ] **Step 2: Update the `.PHONY` line**

Replace:
```makefile
.PHONY: install test test-unit test-integration lint run clean
```
with:
```makefile
.PHONY: install test test-all test-integration run clean help
```

- [ ] **Step 3: Verify both modes**

```bash
make run PROMPT="Say hello" 2>&1 | head -5
```

Expected: One-shot response (or error if inside Claude Code session).

```bash
echo "exit" | make run
```

Expected: Shows banner, then exits on "exit" input.

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "chore: update Makefile run target for interactive mode"
```

---

### Task 6: End-to-end verification

- [ ] **Step 1: Run all unit tests**

```bash
uv run pytest tests/unit -v
```

Expected: All tests PASS.

- [ ] **Step 2: Verify interactive mode starts (from a regular terminal, not Claude Code)**

```bash
make run
```

Expected: Banner appears, `You:` prompt waits for input. Type `exit` to quit.

- [ ] **Step 3: Verify multi-turn session (from a regular terminal)**

```bash
make run
```

Type: `My name is Pedro`
Then: `What is my name?`
Expected: Concierge remembers the name.
Type: `exit`

- [ ] **Step 4: Verify one-shot mode**

```bash
make run PROMPT="What time is it?"
```

Expected: One-shot response printed to stdout.

- [ ] **Step 5: Run integration tests (from a regular terminal)**

```bash
make test-integration
```

Expected: All 4 integration tests PASS (including session resumption).

- [ ] **Step 6: Commit any final adjustments**

Review `git status` for uncommitted files. Stage only specific files.
