# Interactive CLI — Design Spec

**Date:** 2026-03-15
**Status:** Approved
**Author:** Pedro Belfort + Claude

## Purpose

Replace the one-shot CLI with an interactive REPL that provides a rich, conversational experience. Multi-turn session memory lets the user have natural back-and-forth conversations with the concierge.

This picks up "session management" from the foundation spec's "Deliberately Deferred" list.

## Tech Stack Addition

- **`rich`** — Console styling, markdown rendering, spinners, styled panels

## Files Changed

| File | Change |
|------|--------|
| `src/concierge/cli.py` | **New** — Interactive REPL: welcome banner, input loop, spinner, markdown output. Imports `run_concierge` from `agent.py` and `rich` components (`Console`, `Panel`, `Markdown`, `Prompt`, `Status`) |
| `src/concierge/agent.py` | **Modified** — `run_concierge` returns `(result, session_id)`, accepts `session_id` for session resumption. Adds `SystemMessage` import |
| `src/concierge/__main__.py` | **Modified** — No args starts interactive mode; with args stays one-shot. Error handling preserved in both paths |
| `pyproject.toml` | **Modified** — Add `rich` dependency |
| `Makefile` | **Modified** — `run` target uses conditional to omit PROMPT arg when not provided |
| `tests/unit/test_cli.py` | **Modified** — Remove `test_missing_prompt_exits_with_usage` (no-args now starts interactive mode), update mock return type to `(result, session_id)` |
| `tests/unit/test_cli_interactive.py` | **New** — Unit tests for REPL behavior |
| `tests/integration/test_agent.py` | **Modified** — Update return type expectations, add session resumption test |

**Unchanged:** `agents/echo.py`, `tools/time_tool.py`, `tests/unit/test_time_tool.py`

## User Experience

```
╭─────────────────────────────────╮
│  🏠 Concierge                   │
│  Your family assistant          │
│  Type 'exit' or Ctrl+C to quit  │
╰─────────────────────────────────╯

You: What day is it today?

  ⠋ Thinking...

  It's Saturday, March 15th, 2026.

You: What about tomorrow?

  ⠋ Thinking...

  Tomorrow is Sunday, March 16th — perfect for a family outing!

You: exit

Goodbye! 👋
```

- **Welcome banner** — Styled `rich.panel.Panel` with app name
- **`You:` prompt** — `rich.prompt.Prompt.ask()` for input (synchronous, blocks event loop — acceptable for single-user CLI)
- **Spinner** — `rich.status.Status` while the agent is working
- **Markdown response** — `rich.markdown.Markdown` rendering of agent output
- **Session continuity** — Follow-up questions work via Agent SDK session resumption
- **Clean exit** — `exit`, `quit`, Ctrl+C, and Ctrl+D (EOF) all exit gracefully

## Architecture

### `cli.py` — Interactive REPL

Responsible for all UI concerns:
- `run_interactive()` — Async function containing the main loop
- Shows welcome banner on start
- Reads user input in a loop
- Skips empty input
- Calls `run_concierge(prompt, session_id)` with spinner active
- Renders the result as markdown
- Stores `session_id` from first call, passes it on subsequent calls
- Catches errors and displays them without crashing the session

### `agent.py` — Session-Aware Coordinator

`run_concierge` signature changes:

```python
async def run_concierge(prompt: str, session_id: str | None = None) -> tuple[str, str | None]:
```

- Returns `(result_text, session_id)` tuple
- Adds `SystemMessage` to imports from `claude_agent_sdk`
- Two code paths based on `session_id`:

```python
if session_id is None:
    # First call: full config
    options = ClaudeAgentOptions(
        allowed_tools=["Agent", "WebSearch", "WebFetch"],
        agents={"echo": echo_agent},
        mcp_servers={"time": time_server},
        system_prompt=SYSTEM_PROMPT,
        max_turns=10,
    )
else:
    # Resume: session already has tools/agents/prompt
    options = ClaudeAgentOptions(resume=session_id)
```

- Captures `session_id` from `SystemMessage` with `subtype == "init"` via `message.data.get("session_id")`

### `__main__.py` — Mode Router

```python
def main():
    try:
        if len(sys.argv) > 1:
            # One-shot mode
            prompt = " ".join(sys.argv[1:])
            result, _ = asyncio.run(run_concierge(prompt))
            if result:
                print(result)
        else:
            # Interactive mode
            asyncio.run(run_interactive())
    except CLINotFoundError:
        print("Error: Claude Code CLI not found.\n"
              "Install with: pip install claude-agent-sdk", file=sys.stderr)
        sys.exit(1)
    except CLIConnectionError as e:
        print(f"Error: Failed to connect to Claude Code CLI: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
```

Error handling wraps both modes. No `.env` loading needed (Agent SDK uses Claude Code CLI authentication).

### Makefile

The `run` target must conditionally omit the PROMPT argument:

```makefile
run: ## Run the concierge (interactive, or one-shot with PROMPT="...")
ifdef PROMPT
	uv run concierge "$(PROMPT)"
else
	uv run concierge
endif
```

## Error Handling

- **Empty input** — Skip, re-prompt
- **Ctrl+C** — Graceful exit with goodbye message
- **Ctrl+D (EOF)** — Same as exit
- **Agent error mid-session** — Print error in red (`rich` styled), keep session alive for retry
- **Session resumption failure** — Fall back to fresh session, inform user

## Testing

### Unit Tests (`tests/unit/test_cli_interactive.py`)

- Welcome banner renders without error
- Empty input is skipped (no agent call)
- `exit` / `quit` / EOF break the loop
- One-shot mode still works when prompt provided via args

All unit tests mock `run_concierge` — no real agent calls.

### Existing Tests Updates (`tests/unit/test_cli.py`)

- **Remove** `test_missing_prompt_exits_with_usage` — no-args now starts interactive mode instead of exiting
- **Replace with** `test_no_args_starts_interactive` — verify that no-args calls `run_interactive()`
- **Update** `test_valid_args_calls_agent` — mock return type changes to `("response", "session-id")`

### Integration Test Addition (`tests/integration/test_agent.py`)

- Update existing tests for new `(result, session_id)` return type
- Add session resumption test:
  - Call `run_concierge("My name is Pedro")`, get `session_id`
  - Call `run_concierge("What is my name?", session_id=session_id)`
  - Assert the response contains "Pedro"

### Unchanged Tests

- `tests/unit/test_time_tool.py` — No changes needed

## Cert Domains Exercised

- **Domain 1.7:** Session management, resumption via `session_id`, maintaining context across turns
