# Concierge

A personal family concierge agent built with Claude Agent SDK (Python).

## Expectations

You are an expert at building agents with the Claude Agent SDK (Python). You know the SDK's APIs, patterns, and idioms deeply. When working on this project, write idiomatic Agent SDK code confidently — don't hedge, don't suggest alternatives from other frameworks, and don't water down agent architectures into simple API wrappers.

When unsure about a specific SDK detail, use the `/claude-api` skill — it has access to the latest Claude Agent SDK documentation. Prefer this over guessing or reading `.venv/lib/` source. Always verify API signatures before using them.

## Tech Stack

- Python 3.13
- uv (package manager)
- claude-agent-sdk (core dependency)
- rich (interactive CLI / markdown rendering)
- pytest + pytest-asyncio (testing)

## How to Run

```bash
# Install dependencies
uv sync

# Set up your API key
cp .env.example .env
# Edit .env with your actual ANTHROPIC_API_KEY

# Run the concierge (one-shot)
uv run concierge "What time is it?"

# Interactive mode (REPL)
uv run concierge

# Or use Make
make run                    # interactive
make run PROMPT="..."       # one-shot
```

## Running Tests

```bash
# Unit tests (fast, no API key needed)
uv run pytest tests/unit

# Integration tests (requires API key, hits real API)
uv run pytest -m integration
```

## Makefile Targets

- `make test` — unit tests
- `make test-all` — unit + integration
- `make test-integration` — integration only
- `make run` — interactive mode
- `make clean` — remove caches/artifacts

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
- **SDK import convention**: use `import claude_agent_sdk as claude` for functions (`claude.query`, `@claude.tool`, `claude.create_sdk_mcp_server`); use direct imports (`from claude_agent_sdk import ...`) for classes and exceptions (`ClaudeAgentOptions`, `AgentDefinition`, `CLINotFoundError`, etc.). This makes SDK function calls visually distinct from regular Python code.

## Architecture

- `run_concierge()` in `agent.py` is the single entry point — all CLI modes call it
- Uses streaming iteration over `query()` messages (SystemMessage, AssistantMessage, ResultMessage)
- Session continuity via `session_id` (captured from init, passed back on resume)

## Keeping This File Current

This CLAUDE.md is a living document. Update it when:

- **New dependencies** are added to `pyproject.toml` — add them to Tech Stack
- **New subagents** are created in `src/concierge/agents/` — add to Project Structure
- **New tools** are created in `src/concierge/tools/` — add to Project Structure
- **New Makefile targets** are added — add to Makefile Targets
- **New conventions** emerge (naming patterns, test strategies, error handling) — add to Conventions
- **Architecture changes** (new entry points, message types, config patterns) — update Architecture

Do not duplicate what's already obvious from the code. Focus on intent, conventions, and "why" decisions that a future session wouldn't be able to infer from reading the source alone.

## Gotchas & Corrections

Common mistakes Claude Code makes in this project. Add new entries as they're discovered.

- **Don't invent SDK APIs.** `claude-agent-sdk` is a real package with specific imports (`query`, `ClaudeAgentOptions`, `AgentDefinition`, `tool`, `create_sdk_mcp_server`, etc.). Don't fabricate classes or functions that don't exist. When in doubt, read the installed package source.
- **Don't confuse this with the Anthropic Python SDK.** This project uses `claude-agent-sdk` (the Agent SDK), not `anthropic` (the API client). They are different packages with different APIs. Don't import from `anthropic` or use `anthropic.Client`.
- **Don't confuse this with the AI SDK (TypeScript).** The Vercel AI SDK (`ai`, `@ai-sdk/*`) is a completely different ecosystem. Don't apply TypeScript AI SDK patterns, function names, or architecture to this Python project.
- **`query()` is async iterable, not awaitable.** You iterate over it with `async for message in query(...)`, not `result = await query(...)`.
- **Tools return MCP format.** Tool handlers decorated with `@tool` must return `{"content": [{"type": "text", "text": ...}]}`, not plain strings or dicts.
- **`AgentDefinition` is declarative.** Subagents are defined as `AgentDefinition(...)` instances, not classes that extend a base. They declare `description`, `prompt`, and `tools`.
- **`uv run`, not raw `python`.** Always prefix commands with `uv run` to ensure the virtual environment and dependencies are available.
- **This is NOT a Vercel/Next.js/TypeScript project.** Ignore suggestions about Vercel deployment, AI Gateway, Next.js patterns, or npm/pnpm. This is a pure Python CLI agent.

## References

- **`anthropic-docs` MCP server** — configured in `.claude.json`, fetches live docs from Anthropic. Use this to look up SDK APIs before guessing.
- `/claude-api` skill — covers Agent SDK patterns and usage
- [Agent SDK docs](https://docs.anthropic.com/en/docs/claude-code/sdk)
- [Agent SDK source + examples](https://github.com/anthropics/claude-agent-sdk-python)
