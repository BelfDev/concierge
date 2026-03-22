from concierge.agents.restaurant import local_guide, review_scout, vibe_matcher


class TestReviewScout:
    def test_has_web_tools(self):
        assert "WebSearch" in review_scout.tools
        assert "WebFetch" in review_scout.tools

    def test_has_nonempty_description(self):
        assert len(review_scout.description.strip()) > 0

    def test_has_nonempty_prompt(self):
        assert len(review_scout.prompt.strip()) > 0


class TestLocalGuide:
    def test_has_web_tools(self):
        assert "WebSearch" in local_guide.tools
        assert "WebFetch" in local_guide.tools

    def test_has_nonempty_description(self):
        assert len(local_guide.description.strip()) > 0

    def test_has_nonempty_prompt(self):
        assert len(local_guide.prompt.strip()) > 0


class TestVibeMatcher:
    def test_has_web_tools(self):
        assert "WebSearch" in vibe_matcher.tools
        assert "WebFetch" in vibe_matcher.tools

    def test_has_nonempty_description(self):
        assert len(vibe_matcher.description.strip()) > 0

    def test_has_nonempty_prompt(self):
        assert len(vibe_matcher.prompt.strip()) > 0


class TestAgentsAreDistinct:
    def test_descriptions_are_different(self):
        descriptions = {
            review_scout.description,
            local_guide.description,
            vibe_matcher.description,
        }
        assert len(descriptions) == 3
