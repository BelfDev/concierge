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
        result = await run_concierge("Say hello in exactly 3 words.")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_uses_time_tool(self):
        result = await run_concierge(
            "What is the current date? Use your time tool to check."
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_spawns_echo_subagent(self):
        result = await run_concierge(
            "Test the echo subagent by sending it the message 'ping'."
        )
        assert isinstance(result, str)
        assert len(result) > 0
