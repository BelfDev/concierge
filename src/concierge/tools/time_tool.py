import json
from datetime import datetime

from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("get_current_time", "Get the current date, time, day of the week, and timezone", {})
async def get_current_time(args: dict) -> dict:
    now = datetime.now().astimezone()
    result = json.dumps({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "timezone": str(now.tzinfo),
    })
    return {"content": [{"type": "text", "text": result}]}


def create_time_server():
    """Create an MCP server exposing the time tool."""
    return create_sdk_mcp_server("time-tools", tools=[get_current_time])
