from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
)
from claude_agent_sdk.types import StreamEvent
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from concierge.agent import stream_concierge


async def run_interactive() -> None:
    """Run the concierge in interactive REPL mode."""
    console = Console()

    console.print(
        Panel(
            "[bold]🏠 Concierge[/bold]\n"
            "Your family assistant\n"
            "Type 'exit' or Ctrl+C to quit",
            expand=False,
        )
    )
    console.print()

    session_id = None

    while True:
        try:
            user_input = Prompt.ask("[bold]You[/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye! 👋")
            break

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit"):
            console.print("Goodbye! 👋")
            break

        try:
            console.print()
            printed_any = False
            streamed_current_turn = False
            in_tool = False
            thinking = True
            console.print("[dim]Thinking...[/dim]", end="")

            async for message in stream_concierge(user_input, session_id):
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    session_id = message.data.get("session_id")

                elif isinstance(message, StreamEvent):
                    event = message.event
                    event_type = event.get("type")

                    if event_type == "content_block_start":
                        if thinking:
                            print("\r\033[2K", end="", flush=True)
                            thinking = False
                        content_block = event.get("content_block", {})
                        if content_block.get("type") == "tool_use":
                            tool_name = content_block.get("name")
                            console.print(
                                f"  [dim]Using tool: {tool_name}...[/dim]",
                                end="",
                            )
                            in_tool = True

                    elif event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta" and not in_tool:
                            text = delta.get("text", "")
                            if text:
                                print(text, end="", flush=True)
                                streamed_current_turn = True
                                printed_any = True

                    elif event_type == "content_block_stop":
                        if in_tool:
                            console.print(" [dim]done[/dim]")
                            in_tool = False
                        elif streamed_current_turn:
                            print()

                elif isinstance(message, AssistantMessage):
                    if not streamed_current_turn:
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                console.print(Markdown(block.text))
                                printed_any = True
                    streamed_current_turn = False

                elif isinstance(message, ResultMessage):
                    if message.result and not printed_any:
                        console.print(Markdown(message.result))
                        printed_any = True

            if not printed_any:
                console.print("[dim]No response.[/dim]")
            console.print()

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            session_id = None  # Reset to fresh session on error
            console.print("[dim]Starting fresh session. Try again.[/dim]")
            console.print()
