from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from concierge.agent import run_concierge


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
            with console.status("Thinking...", spinner="dots"):
                result, session_id = await run_concierge(
                    user_input, session_id=session_id
                )

            if result:
                console.print()
                console.print(Markdown(result))
            else:
                console.print("[dim]No response.[/dim]")
            console.print()

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            session_id = None  # Reset to fresh session on error
            console.print("[dim]Starting fresh session. Try again.[/dim]")
            console.print()
