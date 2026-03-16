import json
from typing import Any, Optional

from rich.console import Console
from rich.style import Style
from rich.text import Text

console = Console()
err_console = Console(stderr=True)

# Styles
POSITIVE = Style(color="green")
NEGATIVE = Style(color="red")
DIM = Style(dim=True)
BOLD = Style(bold=True)


def format_currency(value: Optional[float], symbol: str = "$") -> str:
    """Format a float as a currency string."""
    if value is None:
        return "—"
    return f"{symbol}{value:,.2f}"


def format_change(value: Optional[float]) -> str:
    """Format a dollar change value with sign."""
    if value is None:
        return "—"
    if value >= 0:
        return f"+${value:,.2f}"
    return f"-${abs(value):,.2f}"


def format_percent(value: Optional[float]) -> str:
    """Format a percentage value with sign."""
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def styled_change(value: Optional[float], formatted: str) -> Text:
    """Return a Rich Text object colored by sign."""
    if value is None:
        return Text("—", style=DIM)
    style = POSITIVE if value >= 0 else NEGATIVE
    return Text(formatted, style=style)


def print_json(data: Any) -> None:
    """Print data as pretty JSON."""
    console.print_json(json.dumps(data))


def error(message: str) -> None:
    """Print an error message to stderr."""
    err_console.print(f"[red]Error:[/red] {message}")
