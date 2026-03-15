from datetime import datetime

from concierge.tools.time_tool import get_current_time


class TestGetCurrentTime:
    async def test_returns_expected_keys(self):
        result = await get_current_time.handler({})
        content = result["content"]
        assert len(content) == 1
        text = content[0]["text"]
        assert "date" in text
        assert "time" in text
        assert "day_of_week" in text
        assert "timezone" in text

    async def test_date_matches_today(self):
        result = await get_current_time.handler({})
        text = result["content"][0]["text"]
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in text

    async def test_day_of_week_is_valid(self):
        result = await get_current_time.handler({})
        text = result["content"][0]["text"]
        valid_days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        assert any(day in text for day in valid_days)
