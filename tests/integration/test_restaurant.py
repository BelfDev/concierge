import os

import pytest

from concierge.agent import run_concierge


@pytest.mark.integration
class TestRestaurantRecommendation:
    @pytest.fixture(autouse=True)
    def skip_inside_claude(self):
        if os.environ.get("CLAUDECODE"):
            pytest.skip("Cannot run integration tests inside Claude Code session")

    async def test_returns_restaurant_recommendations(self):
        result, session_id = await run_concierge(
            "Find me a good Italian restaurant for dinner tonight near Kreuzberg, "
            "mid-range budget, party of 2"
        )
        assert result, "Expected non-empty result"
        assert session_id, "Expected a session_id"
        # The result should mention at least one concrete recommendation
        result_lower = result.lower()
        assert any(
            keyword in result_lower
            for keyword in ["restaurant", "option", "recommend"]
        ), f"Expected restaurant-related content, got: {result[:200]}"
