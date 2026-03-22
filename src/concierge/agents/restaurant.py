from claude_agent_sdk import AgentDefinition

from concierge.prompts.restaurant import (
    LOCAL_GUIDE_DESCRIPTION,
    LOCAL_GUIDE_PROMPT,
    REVIEW_SCOUT_DESCRIPTION,
    REVIEW_SCOUT_PROMPT,
    VIBE_MATCHER_DESCRIPTION,
    VIBE_MATCHER_PROMPT,
)

review_scout = AgentDefinition(
    description=REVIEW_SCOUT_DESCRIPTION,
    prompt=REVIEW_SCOUT_PROMPT,
    tools=["WebSearch", "WebFetch"],
)

local_guide = AgentDefinition(
    description=LOCAL_GUIDE_DESCRIPTION,
    prompt=LOCAL_GUIDE_PROMPT,
    tools=["WebSearch", "WebFetch"],
)

vibe_matcher = AgentDefinition(
    description=VIBE_MATCHER_DESCRIPTION,
    prompt=VIBE_MATCHER_PROMPT,
    tools=["WebSearch", "WebFetch"],
)
