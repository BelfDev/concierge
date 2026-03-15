from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
)

from concierge.agents.echo import echo_agent
from concierge.tools.time_tool import create_time_server

SYSTEM_PROMPT = """\
You are a helpful family concierge assistant. You help with planning, \
scheduling, and answering questions for a family living in Berlin, Germany.

You have access to:
- A time tool that tells you the current date, time, and day of the week
- Web search and fetch for looking up information
- An echo subagent for testing (invoke it only when explicitly asked to test subagents)

Be concise, practical, and friendly.\
"""


async def run_concierge(
    prompt: str, session_id: str | None = None
) -> tuple[str, str | None]:
    """Run the concierge coordinator agent with the given prompt.

    Args:
        prompt: The user's input.
        session_id: If provided, resumes a previous session for multi-turn context.

    Returns:
        A tuple of (result_text, session_id). The session_id can be passed
        to subsequent calls to maintain conversation context.
    """
    if session_id is None:
        time_server = create_time_server()
        options = ClaudeAgentOptions(
            allowed_tools=["Agent", "WebSearch", "WebFetch"],
            agents={"echo": echo_agent},
            mcp_servers={"time": time_server},
            system_prompt=SYSTEM_PROMPT,
            max_turns=10,
        )
    else:
        options = ClaudeAgentOptions(resume=session_id)

    result_text = ""
    captured_session_id = session_id

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            captured_session_id = message.data.get("session_id")
        elif isinstance(message, ResultMessage) and message.result:
            result_text = message.result
        elif isinstance(message, AssistantMessage):
            texts = [
                block.text
                for block in message.content
                if isinstance(block, TextBlock)
            ]
            if texts:
                result_text = "\n".join(texts)

    return result_text, captured_session_id
