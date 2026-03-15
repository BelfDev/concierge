# Concierge

A personal family concierge agent built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python).

The concierge can answer questions, use tools (like checking the current time), and delegate tasks to specialized subagents.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://claude.com/claude-code) installed and authenticated (the Agent SDK uses the CLI under the hood)

## Setup

```bash
git clone <repo-url>
cd concierge
make install
```

## Usage

```bash
# Ask the concierge anything
make run PROMPT="What day of the week is it?"

# Or directly
uv run concierge "Tell me the current time"
```

## Development

```bash
make install          # Install dependencies
make test             # Run unit tests (fast, <1s)
make test-integration # Integration tests (slow, spawns real agent sessions)
make test-all         # Run everything (unit + integration)
make clean            # Remove caches and build artifacts
make help             # Show all available commands
```

> **Note:** Integration tests spawn real Claude Code agent sessions, so they take ~30-40s total. Use `make test` for quick feedback during development.

## Architecture

The concierge uses a coordinator-subagent pattern:

1. **Coordinator** receives user input and decides how to handle it
2. **Subagents** handle specialized tasks (spawned on demand)
3. **Custom MCP tools** provide capabilities like checking the current time

Built with `claude-agent-sdk` using `query()` for the agentic loop and `AgentDefinition` for subagents.
