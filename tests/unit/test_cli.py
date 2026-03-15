import sys
from unittest.mock import patch, AsyncMock

import pytest

from concierge.__main__ import main


class TestCliArgParsing:
    def test_missing_prompt_exits_with_usage(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["concierge"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Usage:" in capsys.readouterr().err

    def test_valid_args_calls_agent(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["concierge", "hello", "world"])
        with patch("concierge.__main__.run_concierge", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "response"
            main()
            mock_run.assert_called_once_with("hello world")
