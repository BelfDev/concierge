from concierge.prompts.restaurant import (
    LOCAL_GUIDE_DESCRIPTION,
    LOCAL_GUIDE_PROMPT,
    RESTAURANT_COORDINATOR_SECTION,
    REVIEW_SCOUT_DESCRIPTION,
    REVIEW_SCOUT_PROMPT,
    VIBE_MATCHER_DESCRIPTION,
    VIBE_MATCHER_PROMPT,
)


class TestRestaurantCoordinatorSection:
    def test_mentions_default_address(self):
        assert "Dora-Benjamin-Park 18" in RESTAURANT_COORDINATOR_SECTION

    def test_mentions_all_three_subagents(self):
        assert "review_scout" in RESTAURANT_COORDINATOR_SECTION
        assert "local_guide" in RESTAURANT_COORDINATOR_SECTION
        assert "vibe_matcher" in RESTAURANT_COORDINATOR_SECTION

    def test_mentions_clarifying_questions(self):
        assert "clarif" in RESTAURANT_COORDINATOR_SECTION.lower()

    def test_mentions_recommended(self):
        assert "Recommended" in RESTAURANT_COORDINATOR_SECTION

    def test_is_nonempty(self):
        assert len(RESTAURANT_COORDINATOR_SECTION.strip()) > 0


class TestReviewScoutPrompts:
    def test_description_is_nonempty(self):
        assert len(REVIEW_SCOUT_DESCRIPTION.strip()) > 0

    def test_prompt_is_nonempty(self):
        assert len(REVIEW_SCOUT_PROMPT.strip()) > 0

    def test_description_mentions_review_platforms(self):
        desc = REVIEW_SCOUT_DESCRIPTION.lower()
        assert any(
            platform in desc
            for platform in ["google", "tripadvisor", "yelp"]
        )

    def test_prompt_mentions_ratings(self):
        assert "rating" in REVIEW_SCOUT_PROMPT.lower()


class TestLocalGuidePrompts:
    def test_description_is_nonempty(self):
        assert len(LOCAL_GUIDE_DESCRIPTION.strip()) > 0

    def test_prompt_is_nonempty(self):
        assert len(LOCAL_GUIDE_PROMPT.strip()) > 0

    def test_description_mentions_blogs_or_guides(self):
        desc = LOCAL_GUIDE_DESCRIPTION.lower()
        assert "blog" in desc or "guide" in desc

    def test_prompt_mentions_hidden_gems(self):
        assert "hidden gem" in LOCAL_GUIDE_PROMPT.lower()


class TestVibeMatcherPrompts:
    def test_description_is_nonempty(self):
        assert len(VIBE_MATCHER_DESCRIPTION.strip()) > 0

    def test_prompt_is_nonempty(self):
        assert len(VIBE_MATCHER_PROMPT.strip()) > 0

    def test_description_mentions_atmosphere(self):
        desc = VIBE_MATCHER_DESCRIPTION.lower()
        assert "atmosphere" in desc or "ambiance" in desc or "vibe" in desc

    def test_prompt_mentions_occasion(self):
        assert "occasion" in VIBE_MATCHER_PROMPT.lower()


class TestPromptsAreDistinct:
    def test_descriptions_are_all_different(self):
        descriptions = {
            REVIEW_SCOUT_DESCRIPTION,
            LOCAL_GUIDE_DESCRIPTION,
            VIBE_MATCHER_DESCRIPTION,
        }
        assert len(descriptions) == 3

    def test_prompts_are_all_different(self):
        prompts = {
            REVIEW_SCOUT_PROMPT,
            LOCAL_GUIDE_PROMPT,
            VIBE_MATCHER_PROMPT,
        }
        assert len(prompts) == 3
