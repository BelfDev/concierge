from claude_agent_sdk import AgentDefinition

from concierge.prompts import ECHO_DESCRIPTION, ECHO_PROMPT

echo_agent = AgentDefinition(
    description=ECHO_DESCRIPTION,
    prompt=ECHO_PROMPT,
    tools=["Read"],
)
