from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.containers import Vertical, Horizontal
from textual import work
from yt_agent.agent import YtAgent


class YtAgentApp(App):
    """A Textual app for the yt-agent."""

    CSS = """
    Screen {
        layout: vertical;
    }
    
    RichLog {
        height: 1fr;
        border: solid green;
        overflow-y: scroll;
        padding: 1;
    }

    Input {
        dock: bottom;
        margin: 1 1;
    }
    """

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, agent: YtAgent = None):
        super().__init__()
        # If agent is passed, use it, otherwise create new one.
        # Note: YtAgent creation might take a moment due to cache check.
        self.temp_agent = agent
        self.agent = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        yield Input(placeholder="Ask yt-agent a question...", id="input")
        yield Footer()

    def on_mount(self) -> None:
        if self.temp_agent:
            self.agent = self.temp_agent
        else:
            self.agent = YtAgent()

        log = self.query_one("#chat-log", RichLog)
        log.write("[bold green]Welcome to yt-agent![/bold green]")
        log.write(f"Using model: [cyan]{self.agent.model_name}[/cyan]")

        if (
            hasattr(self.agent, "cached_content_name")
            and self.agent.cached_content_name
        ):
            log.write(
                f"Cache active: [yellow]{self.agent.cached_content_name}[/yellow]"
            )

        log.write("Type your query below. Press Ctrl+Q to quit.")
        self.query_one("#input").focus()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        query = message.value.strip()
        if not query:
            return

        input_widget = self.query_one("#input", Input)
        input_widget.value = ""

        log = self.query_one("#chat-log", RichLog)
        log.write(f"\n[bold blue]User:[/bold blue] {query}")

        # Start worker
        self.run_query_worker(query)

    @work(exclusive=True, thread=True)
    def run_query_worker(self, query: str) -> None:
        """Run the agent query in a worker thread."""
        try:
            # Synchronous call to agent
            code = self.agent.generate_code(query)

            # Update UI on main thread
            self.app.call_from_thread(self.update_log_with_code, code)

        except Exception as e:
            self.app.call_from_thread(self.update_log_with_error, str(e))

    def update_log_with_code(self, code: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("\n[bold purple]Agent (Generated Code):[/bold purple]")
        log.write(f"```python\n{code}\n```")
        log.write("\n[dim]To execute, copy the code to a notebook or script.[/dim]")

    def update_log_with_error(self, error_msg: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold red]Error:[/bold red] {error_msg}")


if __name__ == "__main__":
    # For testing directly: python -m yt_agent.tui
    try:
        app = YtAgentApp()
        app.run()
    except ImportError:
        print("Please run from project root using: python -m yt_agent.tui")
