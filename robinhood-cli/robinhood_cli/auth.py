import json
from pathlib import Path
from typing import Optional

import typer

from robinhood_core.client import RobinhoodClient
from robinhood_core.errors import AuthRequiredError
from robinhood_cli.output import console, error

DEFAULT_SESSION_DIR = Path.home() / ".config" / "robinhood"
_CONFIG_FILENAME = "config.json"


def load_config(config_dir: Path = DEFAULT_SESSION_DIR) -> Optional[dict]:
    """Load saved CLI config (username etc.). Returns None if not found."""
    config_file = config_dir / _CONFIG_FILENAME
    if not config_file.exists():
        return None
    try:
        return json.loads(config_file.read_text())
    except Exception:
        return None


def save_config(data: dict, config_dir: Path = DEFAULT_SESSION_DIR) -> None:
    """Save CLI config to disk."""
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / _CONFIG_FILENAME
    config_file.write_text(json.dumps(data, indent=2))
    config_file.chmod(0o600)


def get_client(session_dir: Path = DEFAULT_SESSION_DIR) -> RobinhoodClient:
    """Return an authenticated RobinhoodClient using the saved session.

    Exits with a helpful message if the user hasn't run 'rh login' yet.
    """
    config = load_config(config_dir=session_dir)
    if config is None:
        error("Not logged in. Run 'rh login' to authenticate.")
        raise typer.Exit(1)

    client = RobinhoodClient(session_path=str(session_dir))
    try:
        client.ensure_session()
    except AuthRequiredError:
        error("Session expired or invalid. Run 'rh login' to re-authenticate.")
        raise typer.Exit(1)

    return client


# ── CLI commands ──────────────────────────────────────────────────────────────

def login_command() -> None:
    """Authenticate with Robinhood and save a session."""
    console.print("[bold]Robinhood Login[/bold]")
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    DEFAULT_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    client = RobinhoodClient(
        username=username,
        password=password,
        session_path=str(DEFAULT_SESSION_DIR),
        allow_mfa=True,
    )

    mfa_code: Optional[str] = None
    try:
        client.ensure_session(mfa_code=mfa_code)
    except AuthRequiredError as e:
        if "challenge" in str(e).lower() or "mfa" in str(e).lower():
            mfa_code = typer.prompt("MFA / 2FA code")
            try:
                client.ensure_session(mfa_code=mfa_code)
            except AuthRequiredError as e2:
                error(str(e2))
                raise typer.Exit(1)
        else:
            error(str(e))
            raise typer.Exit(1)

    save_config({"username": username})
    console.print(f"[green]✓[/green] Logged in as [bold]{username}[/bold]")
    console.print(f"  Session saved to {DEFAULT_SESSION_DIR}")


def logout_command() -> None:
    """Clear the saved Robinhood session."""
    config = load_config()
    if config is None:
        console.print("Not logged in.")
        return

    client = RobinhoodClient(session_path=str(DEFAULT_SESSION_DIR))
    client.logout()

    config_file = DEFAULT_SESSION_DIR / _CONFIG_FILENAME
    config_file.unlink(missing_ok=True)
    console.print("[green]✓[/green] Logged out.")


def status_command() -> None:
    """Show authentication status."""
    config = load_config()
    if config is None:
        console.print("[yellow]Not logged in.[/yellow] Run [bold]rh login[/bold].")
        return

    username = config.get("username", "unknown")
    pickle_path = DEFAULT_SESSION_DIR / "robinhood.pickle"
    console.print(f"Logged in as [bold]{username}[/bold]")
    console.print(f"Session file: {pickle_path}")
    console.print(
        f"  Exists: {'[green]yes[/green]' if pickle_path.exists() else '[red]no[/red]'}"
    )
