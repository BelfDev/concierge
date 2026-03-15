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
