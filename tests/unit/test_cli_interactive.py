from unittest.mock import patch, AsyncMock, MagicMock

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
            assert mock_run.call_count == 2
