from unittest.mock import patch, MagicMock

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
)
from claude_agent_sdk.types import StreamEvent

from concierge.agent import run_concierge, stream_concierge


def _init_message(sid="session-abc"):
    msg = SystemMessage.__new__(SystemMessage)
    msg.subtype = "init"
    msg.data = {"session_id": sid}
    return msg


def _assistant_message(text):
    block = TextBlock.__new__(TextBlock)
    block.text = text
    msg = AssistantMessage.__new__(AssistantMessage)
    msg.content = [block]
    return msg


def _result_message(text):
    msg = ResultMessage.__new__(ResultMessage)
    msg.result = text
    msg.subtype = "end_turn"
    return msg


def _stream_event(event: dict):
    msg = StreamEvent.__new__(StreamEvent)
    msg.event = event
    msg.uuid = "test-uuid"
    msg.session_id = "session-abc"
    msg.parent_tool_use_id = None
    return msg


async def _fake_query(*, prompt, options):
    """Fake claude.query that yields a minimal message sequence."""
    yield _init_message()
    yield _stream_event({"type": "content_block_start", "content_block": {"type": "text"}})
    yield _stream_event({
        "type": "content_block_delta",
        "delta": {"type": "text_delta", "text": "Hello!"},
    })
    yield _stream_event({"type": "content_block_stop"})
    yield _assistant_message("Hello!")
    yield _result_message("Hello!")


class TestRunConcierge:
    """Tests for run_concierge (batch mode)."""

    async def test_returns_result_text_and_session_id(self):
        with patch("concierge.agent.claude.query", side_effect=_fake_query):
            result, session_id = await run_concierge("hi")
        assert result == "Hello!"
        assert session_id == "session-abc"

    async def test_prefers_result_message_over_assistant(self):
        """ResultMessage.result should be the final value when present."""
        async def query(*, prompt, options):
            yield _init_message()
            yield _assistant_message("from assistant")
            yield _result_message("from result")

        with patch("concierge.agent.claude.query", side_effect=query):
            result, _ = await run_concierge("hi")
        assert result == "from result"

    async def test_falls_back_to_assistant_text(self):
        """If ResultMessage has no result, use AssistantMessage text."""
        async def query(*, prompt, options):
            yield _init_message()
            yield _assistant_message("assistant text")
            empty_result = ResultMessage.__new__(ResultMessage)
            empty_result.result = None
            empty_result.subtype = "end_turn"
            yield empty_result

        with patch("concierge.agent.claude.query", side_effect=query):
            result, _ = await run_concierge("hi")
        assert result == "assistant text"

    async def test_skips_stream_events(self):
        """run_concierge should ignore StreamEvent messages."""
        with patch("concierge.agent.claude.query", side_effect=_fake_query):
            result, _ = await run_concierge("hi")
        # Should still get the final result, not crash on StreamEvents
        assert result == "Hello!"

    async def test_new_session_sets_include_partial_messages(self):
        """First call (no session_id) should set include_partial_messages=True."""
        captured_options = {}

        async def query(*, prompt, options):
            captured_options["opts"] = options
            yield _init_message()
            yield _result_message("ok")

        with patch("concierge.agent.claude.query", side_effect=query):
            await run_concierge("hi")

        assert captured_options["opts"].include_partial_messages is True

    async def test_registers_restaurant_subagents(self):
        """New session should register all three restaurant subagents."""
        captured_options = {}

        async def query(*, prompt, options):
            captured_options["opts"] = options
            yield _init_message()
            yield _result_message("ok")

        with patch("concierge.agent.claude.query", side_effect=query):
            await run_concierge("hi")

        agents = captured_options["opts"].agents
        assert "review_scout" in agents
        assert "local_guide" in agents
        assert "vibe_matcher" in agents

    async def test_max_turns_sufficient_for_restaurant_flow(self):
        """max_turns should be high enough for 3 subagent invocations + clarification."""
        captured_options = {}

        async def query(*, prompt, options):
            captured_options["opts"] = options
            yield _init_message()
            yield _result_message("ok")

        with patch("concierge.agent.claude.query", side_effect=query):
            await run_concierge("hi")

        assert captured_options["opts"].max_turns >= 15

    async def test_resumed_session_sets_include_partial_messages(self):
        """Resumed session should also set include_partial_messages=True."""
        captured_options = {}

        async def query(*, prompt, options):
            captured_options["opts"] = options
            yield _init_message()
            yield _result_message("ok")

        with patch("concierge.agent.claude.query", side_effect=query):
            await run_concierge("hi", session_id="existing-session")

        assert captured_options["opts"].include_partial_messages is True
        assert captured_options["opts"].resume == "existing-session"


class TestStreamConcierge:
    """Tests for stream_concierge (streaming mode)."""

    async def test_yields_all_message_types(self):
        """stream_concierge should pass through all message types from the SDK."""
        with patch("concierge.agent.claude.query", side_effect=_fake_query):
            types_seen = set()
            async for message in stream_concierge("hi"):
                types_seen.add(type(message).__name__)

        assert "SystemMessage" in types_seen
        assert "StreamEvent" in types_seen
        assert "AssistantMessage" in types_seen
        assert "ResultMessage" in types_seen

    async def test_yields_messages_in_order(self):
        """Messages should arrive in the same order the SDK yields them."""
        with patch("concierge.agent.claude.query", side_effect=_fake_query):
            types_in_order = []
            async for message in stream_concierge("hi"):
                types_in_order.append(type(message).__name__)

        assert types_in_order[0] == "SystemMessage"
        assert types_in_order[-1] == "ResultMessage"
        assert "StreamEvent" in types_in_order
