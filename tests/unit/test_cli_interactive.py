from unittest.mock import patch, MagicMock

from claude_agent_sdk import AssistantMessage, ResultMessage, SystemMessage, TextBlock

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
