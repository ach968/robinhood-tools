from typing import Annotated, Optional

import typer
from rich.table import Table

from robinhood_core.services.options import OptionsService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, format_currency, print_json


def _contract_to_row(c) -> list:
    return [
        c.symbol,
        c.expiration,
        format_currency(c.strike, symbol="$"),
        c.type,
        format_currency(c.bid) if c.bid is not None else "—",
        format_currency(c.ask) if c.ask is not None else "—",
        f"{c.delta:.3f}" if c.delta is not None else "—",
        f"{c.implied_volatility:.1%}" if c.implied_volatility is not None else "—",
    ]


def options_chain_command(
    symbol: Annotated[str, typer.Argument(help="Ticker symbol")],
    expiry: Annotated[Optional[str], typer.Option("--expiry", help="Expiration date YYYY-MM-DD")] = None,
    option_type: Annotated[Optional[str], typer.Option("--type", help="call or put")] = None,
    strike: Annotated[Optional[str], typer.Option("--strike", help="Strike price for full Greeks lookup")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Options chain (add --strike for full Greeks and bid/ask)."""
    client = get_client()
    svc = OptionsService(client)
    contracts = svc.get_options_chain(symbol, expiry, option_type, strike)

    if json_output:
        print_json([c.model_dump() for c in contracts])
        return

    if not contracts:
        console.print("No contracts found.")
        return

    has_greeks = any(c.delta is not None for c in contracts)
    table = Table(show_header=True, header_style="bold", title=f"{symbol} Options Chain")
    table.add_column("Symbol")
    table.add_column("Expiry")
    table.add_column("Strike", justify="right")
    table.add_column("Type")

    if has_greeks:
        table.add_column("Bid", justify="right")
        table.add_column("Ask", justify="right")
        table.add_column("Delta", justify="right")
        table.add_column("IV", justify="right")

    for c in contracts:
        row = _contract_to_row(c)
        if has_greeks:
            table.add_row(*row)
        else:
            table.add_row(*row[:4])

    console.print(table)
    if not has_greeks:
        console.print(f"[dim]Tip: use --strike <price> to fetch full Greeks and bid/ask[/dim]")


def options_positions_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Open options positions."""
    client = get_client()
    svc = OptionsService(client)
    positions = svc.get_option_positions()

    if json_output:
        print_json([p.model_dump() for p in positions])
        return

    if not positions:
        console.print("No open options positions.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Symbol")
    table.add_column("Type")
    table.add_column("Strike", justify="right")
    table.add_column("Expiry")
    table.add_column("Direction")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")

    for p in positions:
        table.add_row(
            p.symbol or "—",
            p.option_type or "—",
            format_currency(p.strike_price),
            p.expiration_date or "—",
            p.direction or "—",
            f"{p.quantity:.4g}" if p.quantity else "—",
            format_currency(p.average_price),
        )

    console.print(table)


COMMANDS = [
    (options_chain_command, "options-chain", "Options chain (add --strike for Greeks)"),
    (options_positions_command, "options-positions", "Open options positions"),
]
