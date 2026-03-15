from claude_agent_sdk import AgentDefinition

echo_agent = AgentDefinition(
    description="A simple echo agent for testing subagent spawning. "
    "Use this agent when asked to test or verify the subagent system.",
    prompt="You are a simple echo agent. When you receive a message, "
    "acknowledge it and repeat back what was asked. Be brief and friendly.",
    tools=["Read"],
)
