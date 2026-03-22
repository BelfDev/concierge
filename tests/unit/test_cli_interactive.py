from unittest.mock import patch, MagicMock, call

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock
from claude_agent_sdk.types import StreamEvent

from concierge.cli import run_interactive


def _make_stream(*messages):
    """Create an async iterator that yields the given messages."""
    async def stream(prompt, session_id=None):
        for msg in messages:
            yield msg
    return stream


def _init_message(sid="session-123"):
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
    msg.session_id = "session-123"
    msg.parent_tool_use_id = None
    return msg


def _text_delta_events(text: str):
    """Generate the StreamEvent sequence for a streamed text block."""
    return [
        _stream_event({"type": "content_block_start", "content_block": {"type": "text"}}),
        *[
            _stream_event({
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": word + " "},
            })
            for word in text.split()
        ],
        _stream_event({"type": "content_block_stop"}),
    ]


def _tool_use_events(tool_name: str):
    """Generate the StreamEvent sequence for a tool call."""
    return [
        _stream_event({
            "type": "content_block_start",
            "content_block": {"type": "tool_use", "name": tool_name},
        }),
        _stream_event({"type": "content_block_stop"}),
    ]


# ---------------------------------------------------------------------------
# REPL basics
# ---------------------------------------------------------------------------


class TestInteractiveRepl:
    async def test_exit_command_breaks_loop(self):
        mock_console = MagicMock()
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
        ):
            mock_prompt_cls.ask.side_effect = ["exit"]
            await run_interactive()

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
            patch("concierge.cli.stream_concierge") as mock_stream,
        ):
            mock_prompt_cls.ask.side_effect = ["", "   ", "exit"]
            await run_interactive()
            mock_stream.assert_not_called()

    async def test_sends_prompt_to_agent(self):
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            _assistant_message("hello back"),
            _result_message("hello back"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream) as mock_stream,
        ):
            mock_prompt_cls.ask.side_effect = ["hello", "exit"]
            await run_interactive()
            mock_stream.assert_called_once_with("hello", None)

    async def test_passes_session_id_on_second_call(self):
        mock_console = MagicMock()
        call_count = 0

        def make_stream(prompt, session_id=None):
            nonlocal call_count
            call_count += 1
            return _make_stream(
                _init_message("session-123"),
                _assistant_message(f"response {call_count}"),
                _result_message(f"response {call_count}"),
            )(prompt, session_id)

        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=make_stream) as mock_stream,
        ):
            mock_prompt_cls.ask.side_effect = ["first", "second", "exit"]
            await run_interactive()
            assert mock_stream.call_count == 2
            mock_stream.assert_any_call("first", None)
            mock_stream.assert_any_call("second", "session-123")

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
        first_print_arg = mock_console.print.call_args_list[0][0][0]
        from rich.panel import Panel
        assert isinstance(first_print_arg, Panel)

    async def test_agent_error_keeps_session_alive(self):
        mock_console = MagicMock()
        call_count = 0

        def make_stream(prompt, session_id=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("boom")
            return _make_stream(
                _init_message("session-456"),
                _assistant_message("recovered"),
                _result_message("recovered"),
            )(prompt, session_id)

        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=make_stream) as mock_stream,
        ):
            mock_prompt_cls.ask.side_effect = ["hello", "world", "exit"]
            await run_interactive()
            assert mock_stream.call_count == 2

    async def test_session_reset_on_error(self):
        mock_console = MagicMock()
        call_count = 0

        def make_stream(prompt, session_id=None):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("session expired")
            return _make_stream(
                _init_message("session-123"),
                _assistant_message("ok"),
                _result_message("ok"),
            )(prompt, session_id)

        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=make_stream) as mock_stream,
        ):
            mock_prompt_cls.ask.side_effect = ["first", "second", "exit"]
            await run_interactive()
            assert mock_stream.call_count == 2


# ---------------------------------------------------------------------------
# Streaming output
# ---------------------------------------------------------------------------


class TestStreamingOutput:
    """Tests for StreamEvent-based token streaming in the CLI."""

    async def test_text_deltas_printed_to_stdout(self, capsys):
        """Text delta tokens should be printed directly to stdout."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            *_text_delta_events("hello world"),
            _assistant_message("hello world"),
            _result_message("hello world"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        captured = capsys.readouterr().out
        assert "hello" in captured
        assert "world" in captured

    async def test_streamed_text_suppresses_assistant_message(self, capsys):
        """When text was streamed via StreamEvent, the AssistantMessage
        text should NOT be printed again (no duplicate output)."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            *_text_delta_events("streamed text"),
            _assistant_message("streamed text"),
            _result_message("streamed text"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        # AssistantMessage text should NOT have been rendered via Markdown
        markdown_prints = [
            c for c in mock_console.print.call_args_list
            if c.args and hasattr(c.args[0], "__class__")
            and c.args[0].__class__.__name__ == "Markdown"
        ]
        # The only Markdown prints should NOT contain the streamed text
        for md_call in markdown_prints:
            assert "streamed text" not in str(md_call)

    async def test_assistant_message_renders_when_no_stream_events(self):
        """If no StreamEvent arrived (partial messages disabled/unavailable),
        AssistantMessage text should still render as Markdown."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            _assistant_message("fallback text"),
            _result_message("fallback text"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        # Markdown should have been printed for the assistant text
        from rich.markdown import Markdown
        markdown_prints = [
            c for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], Markdown)
        ]
        assert len(markdown_prints) >= 1

    async def test_tool_use_shows_status(self):
        """Tool calls should show 'Using tool: <name>...' and 'done'."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            *_tool_use_events("get_current_time"),
            _assistant_message("The time is 3pm"),
            _result_message("The time is 3pm"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["what time", "exit"]
            await run_interactive()

        printed_strings = [
            str(c) for c in mock_console.print.call_args_list
        ]
        all_output = " ".join(printed_strings)
        assert "get_current_time" in all_output
        assert "done" in all_output

    async def test_thinking_indicator_shown(self):
        """'Thinking...' should appear before the first content block."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            _assistant_message("response"),
            _result_message("response"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        printed_strings = [
            str(c) for c in mock_console.print.call_args_list
        ]
        all_output = " ".join(printed_strings)
        assert "Thinking" in all_output

    async def test_no_response_shown_when_empty(self):
        """When no text is produced, show 'No response.'."""
        mock_console = MagicMock()
        result = ResultMessage.__new__(ResultMessage)
        result.result = None
        result.subtype = "end_turn"
        stream = _make_stream(
            _init_message(),
            result,
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        printed_strings = [
            str(c) for c in mock_console.print.call_args_list
        ]
        all_output = " ".join(printed_strings)
        assert "No response" in all_output

    async def test_result_message_fallback_when_nothing_printed(self):
        """If nothing was printed via streaming or AssistantMessage,
        ResultMessage.result should be rendered."""
        mock_console = MagicMock()
        # No AssistantMessage, only ResultMessage
        stream = _make_stream(
            _init_message(),
            _result_message("result only"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        from rich.markdown import Markdown
        markdown_prints = [
            c for c in mock_console.print.call_args_list
            if c.args and isinstance(c.args[0], Markdown)
        ]
        assert len(markdown_prints) >= 1

    async def test_text_deltas_suppressed_during_tool_use(self, capsys):
        """Text deltas inside a tool_use block should not be printed."""
        mock_console = MagicMock()
        stream = _make_stream(
            _init_message(),
            # Tool starts
            _stream_event({
                "type": "content_block_start",
                "content_block": {"type": "tool_use", "name": "Read"},
            }),
            # Delta that arrives while in_tool=True
            _stream_event({
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "SHOULD_NOT_APPEAR"},
            }),
            _stream_event({"type": "content_block_stop"}),
            _assistant_message("actual response"),
            _result_message("actual response"),
        )
        with (
            patch("concierge.cli.Console", return_value=mock_console),
            patch("concierge.cli.Prompt") as mock_prompt_cls,
            patch("concierge.cli.stream_concierge", side_effect=stream),
        ):
            mock_prompt_cls.ask.side_effect = ["hi", "exit"]
            await run_interactive()

        captured = capsys.readouterr().out
        assert "SHOULD_NOT_APPEAR" not in captured
