import sys
from unittest.mock import patch, AsyncMock

from concierge.__main__ import main


class TestCliOneShot:
    def test_valid_args_calls_agent(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["concierge", "hello", "world"])
        with patch("concierge.__main__.run_concierge", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = ("response", "session-123")
            main()
            mock_run.assert_called_once_with("hello world")
        assert "response" in capsys.readouterr().out

    def test_no_args_starts_interactive(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["concierge"])
        with patch("concierge.__main__.run_interactive", new_callable=AsyncMock) as mock_interactive:
            main()
            mock_interactive.assert_called_once()
