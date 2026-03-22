import os
import shutil

import pytest

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage
from claude_agent_sdk.types import StreamEvent

from concierge.agent import run_concierge, stream_concierge


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


class TestStreamConcierge:
    """Integration tests for stream_concierge (streaming mode)."""

    async def test_yields_stream_events(self):
        """stream_concierge should yield StreamEvent messages
        when include_partial_messages is True."""
        types_seen = set()
        async for message in stream_concierge("Say hi in one word."):
            types_seen.add(type(message).__name__)

        assert "StreamEvent" in types_seen, (
            "No StreamEvent received — include_partial_messages may not be set"
        )

    async def test_yields_text_deltas(self):
        """At least one text_delta StreamEvent should arrive."""
        text_deltas = []
        async for message in stream_concierge("Say hello."):
            if isinstance(message, StreamEvent):
                event = message.event
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text_deltas.append(delta.get("text", ""))

        assert len(text_deltas) > 0, "No text_delta events received"
        full_text = "".join(text_deltas)
        assert len(full_text) > 0

    async def test_ends_with_result_message(self):
        """The last meaningful message should be a ResultMessage."""
        last_message = None
        async for message in stream_concierge("Say hi."):
            last_message = message

        assert isinstance(last_message, ResultMessage)

    async def test_init_message_has_session_id(self):
        """The SystemMessage init event should contain a session_id."""
        session_id = None
        async for message in stream_concierge("Hi."):
            if isinstance(message, SystemMessage) and message.subtype == "init":
                session_id = message.data.get("session_id")
                break

        assert session_id is not None
