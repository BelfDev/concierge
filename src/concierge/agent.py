from collections.abc import AsyncIterator

import claude_agent_sdk as claude
from claude_agent_sdk import (
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
)
from claude_agent_sdk.types import StreamEvent

from concierge.agents.echo import echo_agent
from concierge.prompts import COORDINATOR_PROMPT
from concierge.tools.time_tool import create_time_server


async def stream_concierge(
    prompt: str, session_id: str | None = None
) -> AsyncIterator[AssistantMessage | ResultMessage | SystemMessage | StreamEvent]:
    """Stream messages from the concierge agent as they arrive.

    Yields each SDK message directly so callers can render
    text blocks, tool calls, and results incrementally.
    """
    if session_id is None:
        time_server = create_time_server()
        options = ClaudeAgentOptions(
            allowed_tools=["Agent", "WebSearch", "WebFetch"],
            agents={"echo": echo_agent},
            mcp_servers={"time": time_server},
            system_prompt=COORDINATOR_PROMPT,
            max_turns=10,
            include_partial_messages=True,
        )
    else:
        options = ClaudeAgentOptions(
            resume=session_id,
            include_partial_messages=True,
        )

    async for message in claude.query(prompt=prompt, options=options):
        yield message


async def run_concierge(
    prompt: str, session_id: str | None = None
) -> tuple[str, str | None]:
    """Run the concierge and return the final result.

    Convenience wrapper over stream_concierge for non-interactive use
    (one-shot CLI, tests, programmatic callers).
    """
    result_text = ""
    captured_session_id = session_id

    async for message in stream_concierge(prompt, session_id):
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
