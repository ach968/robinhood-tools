# Robinhood CLI Implementation Plan

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Extract `robinhood-core` from the MCP server, wire `robinhood-mcp` to depend on it, then build `robinhood-cli` (the `rh` command) on top of the shared core.

**Architecture:** Three packages in a monorepo — `robinhood-core` (shared models, services, client), `robinhood-mcp` (MCP server; imports updated only), `robinhood-cli` (Typer CLI; new). Auth for the CLI uses a saved session pickle at `~/.config/robinhood/`; all commands load it silently after `rh login`.

**Tech Stack:** Python 3.11+, uv, Pydantic v2, robin-stocks, Typer, Rich, pytest

---

## Phase 1 — Extract `robinhood-core` and update `robinhood-mcp`

> After completing all Phase 1 tasks, run the full `robinhood-mcp` test suite before moving to Phase 2.

---

### Task 1: Scaffold `robinhood-core` package

**TDD scenario:** Trivial scaffolding — no tests yet.

**Files:**
- Create: `robinhood-core/pyproject.toml`
- Create: `robinhood-core/robinhood_core/__init__.py`
- Create: `robinhood-core/robinhood_core/models/__init__.py`
- Create: `robinhood-core/robinhood_core/services/__init__.py`
- Create: `robinhood-core/tests/__init__.py`
- Create: `robinhood-core/tests/unit/__init__.py`

**Step 1: Create `robinhood-core/pyproject.toml`**

```toml
[project]
name = "robinhood-core"
version = "0.1.0"
description = "Shared models, services, and client for Robinhood tools"
requires-python = ">=3.11"
dependencies = [
    "robin-stocks>=3.0.0",
    "pydantic>=2.0.0",
    "requests>=2.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
```

**Step 2: Create empty `__init__.py` files**

```bash
mkdir -p robinhood-core/robinhood_core/models
mkdir -p robinhood-core/robinhood_core/services
mkdir -p robinhood-core/tests/unit
touch robinhood-core/robinhood_core/__init__.py
touch robinhood-core/robinhood_core/models/__init__.py
touch robinhood-core/robinhood_core/services/__init__.py
touch robinhood-core/tests/__init__.py
touch robinhood-core/tests/unit/__init__.py
```

**Step 3: Bootstrap a venv with uv**

```bash
cd robinhood-core
uv venv
uv pip install -e ".[dev]"
```

Expected: venv created, package installs cleanly.

**Step 4: Commit**

```bash
git add robinhood-core/
git commit -m "feat(core): scaffold robinhood-core package"
```

---

### Task 2: Copy `errors.py` and `models/` into core

**TDD scenario:** Trivial copy — update imports, copy tests.

**Files:**
- Create: `robinhood-core/robinhood_core/errors.py`
- Create: `robinhood-core/robinhood_core/models/base.py`
- Create: `robinhood-core/robinhood_core/models/market.py`
- Create: `robinhood-core/robinhood_core/models/options.py`
- Create: `robinhood-core/robinhood_core/models/portfolio.py`
- Create: `robinhood-core/robinhood_core/models/watchlists.py`
- Create: `robinhood-core/robinhood_core/models/news.py`
- Create: `robinhood-core/robinhood_core/models/fundamentals.py`
- Create: `robinhood-core/robinhood_core/models/orders.py`

**Step 1: Copy `errors.py` verbatim**

Copy `robinhood-mcp/robin_stocks_mcp/robinhood/errors.py` to `robinhood-core/robinhood_core/errors.py` — no import changes needed.

**Step 2: Copy all model files**

Copy `robinhood-mcp/robin_stocks_mcp/models/base.py` → `robinhood-core/robinhood_core/models/base.py` verbatim.

Copy each model file (`market.py`, `options.py`, `portfolio.py`, `watchlists.py`, `news.py`, `fundamentals.py`, `orders.py`) from `robinhood-mcp/robin_stocks_mcp/models/` → `robinhood-core/robinhood_core/models/`. The only import in each model file is `from .base import ...` — these are relative and need no change.

**Step 3: Update `robinhood-core/robinhood_core/models/__init__.py`**

```python
from .market import Quote, Candle
from .options import OptionContract, OptionPosition
from .portfolio import PortfolioSummary, Position
from .watchlists import Watchlist
from .news import NewsItem
from .fundamentals import Fundamentals
from .orders import CryptoOrder, OptionOrder, OrderExecution, OrderHistory, StockOrder

__all__ = [
    "Quote",
    "Candle",
    "OptionContract",
    "OptionPosition",
    "PortfolioSummary",
    "Position",
    "Watchlist",
    "NewsItem",
    "Fundamentals",
    "OrderHistory",
    "StockOrder",
    "OptionOrder",
    "CryptoOrder",
    "OrderExecution",
]
```

**Step 4: Copy model unit tests**

Copy all test files from `robinhood-mcp/robin_stocks_mcp/tests/unit/test_models_*.py` and `test_model_coercion.py` into `robinhood-core/tests/unit/`. Then do a bulk find-and-replace in each copied test file:

- `from robin_stocks_mcp.models` → `from robinhood_core.models`

**Step 5: Run model tests**

```bash
cd robinhood-core
uv run pytest tests/unit/ -v
```

Expected: All model tests pass.

**Step 6: Commit**

```bash
git add robinhood-core/
git commit -m "feat(core): add errors.py and models"
```

---

### Task 3: Copy `client.py` into core with session-only support

**TDD scenario:** Modifying tested code — we're also changing `ensure_session()` behavior, so add one new test.

**Files:**
- Create: `robinhood-core/robinhood_core/client.py`
- Create: `robinhood-core/tests/unit/test_robinhood_client.py`

**Step 1: Copy `client.py` and update imports**

Copy `robinhood-mcp/robin_stocks_mcp/robinhood/client.py` → `robinhood-core/robinhood_core/client.py`.

Change the import at the top from:
```python
from .errors import AuthRequiredError, NetworkError
```
to:
```python
from robinhood_core.errors import AuthRequiredError, NetworkError
```

**Step 2: Modify `ensure_session()` to support session-only mode**

The CLI will call `ensure_session()` with no username/password — relying on a saved robin_stocks pickle. Currently the client raises `AuthRequiredError` if credentials are missing. Add a pickle-first attempt when `session_path` is set:

Find this block in `ensure_session()`:
```python
        if not self._username or not self._password:
            logger.warning("Authentication failed: missing credentials")
            raise AuthRequiredError(
                "Authentication required. Please set RH_USERNAME and RH_PASSWORD, "
                "or ensure a valid session cache exists. You may need to refresh "
                "your session in the Robinhood app."
            )
```

Replace with:
```python
        if not self._username or not self._password:
            # When no credentials are provided, try to restore from a saved pickle.
            # robin_stocks will use the stored token if still valid.
            if self._session_path:
                try:
                    logger.debug("No credentials provided, trying saved session at %s", self._session_path)
                    login_result = rh.login(
                        username="",
                        password="",
                        pickle_path=self._session_path,
                        store_session=False,
                    )
                    if login_result:
                        self._authenticated = True
                        logger.info("Restored session from saved pickle")
                        return self
                except Exception as e:
                    logger.debug("Failed to restore saved session: %s", e)

            logger.warning("Authentication failed: missing credentials")
            raise AuthRequiredError(
                "Not logged in. Run 'rh login' to authenticate."
            )
```

**Step 3: Copy and update client tests**

Copy `robinhood-mcp/tests/unit/test_robinhood_client.py` → `robinhood-core/tests/unit/test_robinhood_client.py`. Update imports:

- `from robin_stocks_mcp.robinhood.client import RobinhoodClient` → `from robinhood_core.client import RobinhoodClient`
- `from robin_stocks_mcp.robinhood.errors import` → `from robinhood_core.errors import`

**Step 4: Write the new session-only test**

Add to `robinhood-core/tests/unit/test_robinhood_client.py`:

```python
def test_ensure_session_tries_pickle_when_no_credentials():
    """When no credentials are given but session_path is set, try the pickle."""
    from robinhood_core.client import RobinhoodClient

    with patch("robinhood_core.client.rh.login", return_value={"access_token": "tok"}) as mock_login:
        client = RobinhoodClient(session_path="/tmp/fake_session")
        client.ensure_session()
        assert client._authenticated is True
        mock_login.assert_called_once_with(
            username="",
            password="",
            pickle_path="/tmp/fake_session",
            store_session=False,
        )


def test_ensure_session_raises_when_no_credentials_no_session_path():
    from robinhood_core.client import RobinhoodClient
    from robinhood_core.errors import AuthRequiredError

    client = RobinhoodClient()  # no credentials, no session path
    with pytest.raises(AuthRequiredError):
        client.ensure_session()
```

**Step 5: Run tests**

```bash
cd robinhood-core
uv run pytest tests/unit/test_robinhood_client.py -v
```

Expected: All pass.

**Step 6: Commit**

```bash
git add robinhood-core/
git commit -m "feat(core): add RobinhoodClient with session-only restore support"
```

---

### Task 4: Copy all services into core

**TDD scenario:** Modifying tested code — copy and update tests.

**Files:**
- Create: `robinhood-core/robinhood_core/services/fundamentals.py`
- Create: `robinhood-core/robinhood_core/services/market_data.py`
- Create: `robinhood-core/robinhood_core/services/news.py`
- Create: `robinhood-core/robinhood_core/services/options.py`
- Create: `robinhood-core/robinhood_core/services/orders.py`
- Create: `robinhood-core/robinhood_core/services/portfolio.py`
- Create: `robinhood-core/robinhood_core/services/watchlists.py`

**Step 1: Copy all service files**

Copy each file from `robinhood-mcp/robin_stocks_mcp/services/` → `robinhood-core/robinhood_core/services/`.

In each service file, replace all old import paths:
- `from robin_stocks_mcp.models import` → `from robinhood_core.models import`
- `from robin_stocks_mcp.models.orders import` → `from robinhood_core.models.orders import`
- `from robin_stocks_mcp.robinhood.client import` → `from robinhood_core.client import`
- `from robin_stocks_mcp.robinhood.errors import` → `from robinhood_core.errors import`

**Step 2: Update `robinhood-core/robinhood_core/services/__init__.py`**

```python
from .fundamentals import FundamentalsService
from .news import NewsService
from .options import OptionsService
from .portfolio import PortfolioService
from .watchlists import WatchlistsService
from .orders import OrdersService

__all__ = [
    "FundamentalsService",
    "NewsService",
    "OptionsService",
    "OrdersService",
    "PortfolioService",
    "WatchlistsService",
]
```

**Step 3: Copy and update service tests**

Copy all `test_service_*.py` files from `robinhood-mcp/tests/unit/` → `robinhood-core/tests/unit/`.

In each test file replace:
- `from robin_stocks_mcp.services` → `from robinhood_core.services`
- `from robin_stocks_mcp.robinhood.client import` → `from robinhood_core.client import`
- `from robin_stocks_mcp.robinhood.errors import` → `from robinhood_core.errors import`
- `from robin_stocks_mcp.models` → `from robinhood_core.models`

**Step 4: Run all core tests**

```bash
cd robinhood-core
uv run pytest tests/ -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
git add robinhood-core/
git commit -m "feat(core): add all services"
```

---

### Task 5: Update `robinhood-mcp` to depend on `robinhood-core`

**TDD scenario:** Modifying tested code — run existing MCP tests to confirm nothing broke.

**Files:**
- Modify: `robinhood-mcp/pyproject.toml`
- Modify: `robinhood-mcp/robin_stocks_mcp/server.py`
- Modify: `robinhood-mcp/tests/unit/*.py` (import paths)

**Step 1: Update `robinhood-mcp/pyproject.toml`**

Replace the `dependencies` list and add a `[tool.uv.sources]` section:

```toml
dependencies = [
    "mcp>=1.0.0",
    "robinhood-core",
    "pydantic>=2.0.0",
    "requests>=2.25.0",
]

[tool.uv.sources]
robinhood-core = { path = "../robinhood-core", editable = true }
```

Remove `robin-stocks>=3.0.0` from the MCP's own dependencies — it now comes transitively from `robinhood-core`.

**Step 2: Reinstall MCP venv**

```bash
cd robinhood-mcp
uv pip install -e ".[dev]"
```

Expected: Installs cleanly, `robinhood-core` resolved from `../robinhood-core`.

**Step 3: Update `server.py` imports**

In `robinhood-mcp/robin_stocks_mcp/server.py`, replace:
```python
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
    NetworkError,
)
from robin_stocks_mcp.services import (
    FundamentalsService,
    NewsService,
    OptionsService,
    OrdersService,
    PortfolioService,
    WatchlistsService,
)
from robin_stocks_mcp.services.market_data import MarketDataService
```
with:
```python
from robinhood_core.client import RobinhoodClient
from robinhood_core.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
    NetworkError,
)
from robinhood_core.services import (
    FundamentalsService,
    NewsService,
    OptionsService,
    OrdersService,
    PortfolioService,
    WatchlistsService,
)
from robinhood_core.services.market_data import MarketDataService
```

**Step 4: Update MCP test imports**

In every file under `robinhood-mcp/tests/`, replace:
- `from robin_stocks_mcp.robinhood.client import` → `from robinhood_core.client import`
- `from robin_stocks_mcp.robinhood.errors import` → `from robinhood_core.errors import`
- `from robin_stocks_mcp.services` → `from robinhood_core.services`
- `from robin_stocks_mcp.models` → `from robinhood_core.models`

Leave any `from robin_stocks_mcp.server import` lines untouched — `server.py` still lives in the MCP package.

**Step 5: Run full MCP test suite**

```bash
cd robinhood-mcp
uv run pytest tests/ -v
```

Expected: All existing tests pass.

**Step 6: Commit**

```bash
git add robinhood-mcp/
git commit -m "refactor(mcp): import from robinhood-core"
```

---

## ✅ Phase 1 Checkpoint

Before continuing, verify:

```bash
# Core tests
cd robinhood-core && uv run pytest tests/ -v
# MCP tests
cd ../robinhood-mcp && uv run pytest tests/ -v
```

Both suites must be green. Then continue to Phase 2.

---

## Phase 2 — Build `robinhood-cli`

---

### Task 6: Scaffold `robinhood-cli` package

**TDD scenario:** Trivial scaffolding.

**Files:**
- Create: `robinhood-cli/pyproject.toml`
- Create: `robinhood-cli/robinhood_cli/__init__.py`
- Create: `robinhood-cli/robinhood_cli/commands/__init__.py`
- Create: `robinhood-cli/tests/__init__.py`
- Create: `robinhood-cli/tests/unit/__init__.py`

**Step 1: Create `robinhood-cli/pyproject.toml`**

```toml
[project]
name = "robinhood-cli"
version = "0.1.0"
description = "CLI tool for Robinhood via robin-stocks"
requires-python = ">=3.11"
dependencies = [
    "robinhood-core",
    "typer>=0.12.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
rh = "robinhood_cli.main:app"

[tool.uv.sources]
robinhood-core = { path = "../robinhood-core", editable = true }

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
target-version = "py311"
```

**Step 2: Create empty init files and install**

```bash
mkdir -p robinhood-cli/robinhood_cli/commands
mkdir -p robinhood-cli/tests/unit
touch robinhood-cli/robinhood_cli/__init__.py
touch robinhood-cli/robinhood_cli/commands/__init__.py
touch robinhood-cli/tests/__init__.py
touch robinhood-cli/tests/unit/__init__.py
cd robinhood-cli
uv venv
uv pip install -e ".[dev]"
```

Expected: `rh` command available in the venv.

**Step 3: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): scaffold robinhood-cli package"
```

---

### Task 7: Create `output.py` — shared Rich console and `--json` flag

**TDD scenario:** New feature — write a formatter test first.

**Files:**
- Create: `robinhood-cli/robinhood_cli/output.py`
- Create: `robinhood-cli/tests/unit/test_output.py`

**Step 1: Write the failing test**

```python
# robinhood-cli/tests/unit/test_output.py
import json
from robinhood_cli.output import format_currency, format_change, format_percent


def test_format_currency_positive():
    assert format_currency(213.42) == "$213.42"


def test_format_currency_none():
    assert format_currency(None) == "—"


def test_format_change_positive():
    result = format_change(1.84)
    assert "+$1.84" in result


def test_format_change_negative():
    result = format_change(-3.20)
    assert "-$3.20" in result


def test_format_change_none():
    assert format_change(None) == "—"


def test_format_percent_positive():
    result = format_percent(0.87)
    assert "+0.87%" in result


def test_format_percent_negative():
    result = format_percent(-1.27)
    assert "-1.27%" in result
```

**Step 2: Run to confirm failure**

```bash
cd robinhood-cli
uv run pytest tests/unit/test_output.py -v
```

Expected: FAIL — `robinhood_cli.output` not found.

**Step 3: Implement `output.py`**

```python
# robinhood-cli/robinhood_cli/output.py
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
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:,.2f}"


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
```

**Step 4: Run tests**

```bash
uv run pytest tests/unit/test_output.py -v
```

Expected: All pass.

**Step 5: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add output helpers"
```

---

### Task 8: Create `auth.py` — session management + `rh login/logout/status`

**TDD scenario:** New feature — this touches the filesystem; write focused unit tests.

**Files:**
- Create: `robinhood-cli/robinhood_cli/auth.py`
- Create: `robinhood-cli/tests/unit/test_auth.py`

**Step 1: Write the failing tests**

```python
# robinhood-cli/tests/unit/test_auth.py
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_get_session_dir_returns_path():
    from robinhood_cli.auth import DEFAULT_SESSION_DIR
    assert isinstance(DEFAULT_SESSION_DIR, Path)
    assert "robinhood" in str(DEFAULT_SESSION_DIR)


def test_load_config_returns_none_when_missing(tmp_path):
    from robinhood_cli.auth import load_config
    result = load_config(config_dir=tmp_path)
    assert result is None


def test_save_and_load_config(tmp_path):
    from robinhood_cli.auth import save_config, load_config
    save_config({"username": "testuser"}, config_dir=tmp_path)
    result = load_config(config_dir=tmp_path)
    assert result == {"username": "testuser"}


def test_get_client_raises_when_not_logged_in(tmp_path):
    from robinhood_cli.auth import get_client
    import typer
    with pytest.raises(SystemExit):
        get_client(session_dir=tmp_path)
```

**Step 2: Run to confirm failure**

```bash
uv run pytest tests/unit/test_auth.py -v
```

Expected: FAIL.

**Step 3: Implement `auth.py`**

```python
# robinhood-cli/robinhood_cli/auth.py
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
    console.print(f"  Exists: {'[green]yes[/green]' if pickle_path.exists() else '[red]no[/red]'}")
```

**Step 4: Run tests**

```bash
uv run pytest tests/unit/test_auth.py -v
```

Expected: All pass.

**Step 5: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add session auth helpers and login/logout/status commands"
```

---

### Task 9: Create `main.py` — Typer app entry point

**TDD scenario:** Trivial wiring — no separate test needed; verified by running `rh --help`.

**Files:**
- Create: `robinhood-cli/robinhood_cli/main.py`

**Step 1: Implement `main.py`**

```python
# robinhood-cli/robinhood_cli/main.py
import typer

from robinhood_cli.auth import login_command, logout_command, status_command

app = typer.Typer(
    name="rh",
    help="Robinhood CLI — market data, portfolio, options, and more.",
    no_args_is_help=True,
)

# Auth commands
app.command("login", help="Authenticate with Robinhood")(login_command)
app.command("logout", help="Clear the saved session")(logout_command)
app.command("status", help="Show authentication status")(status_command)

# Command modules are registered after import to avoid circular deps.
# Each module appends its commands to `app` on import.
def _register_commands() -> None:
    from robinhood_cli.commands import market, portfolio, options, watchlists, news, fundamentals, orders
    for cmd_fn, name, help_text in market.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in portfolio.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in options.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in watchlists.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in news.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in fundamentals.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)
    for cmd_fn, name, help_text in orders.COMMANDS:
        app.command(name, help=help_text)(cmd_fn)


_register_commands()

if __name__ == "__main__":
    app()
```

> **Note:** Each command module exposes a `COMMANDS` list of `(function, name, help_text)` tuples. This keeps `main.py` thin and avoids having to import `typer` in every command file just to call `app.command()`.

**Step 2: Verify `rh --help` works**

```bash
cd robinhood-cli
uv run rh --help
```

Expected: Help text printed with `login`, `logout`, `status` listed. (Other commands will be listed after subsequent tasks.)

**Step 3: Commit**

```bash
git add robinhood-cli/robinhood_cli/main.py
git commit -m "feat(cli): add main Typer app entry point"
```

---

### Task 10: Create market commands — `rh price`, `rh quote`, `rh history`

**TDD scenario:** New feature — write a formatter test first, then implement.

**Files:**
- Create: `robinhood-cli/robinhood_cli/commands/market.py`
- Create: `robinhood-cli/tests/unit/test_commands_market.py`

**Step 1: Write the failing formatter test**

```python
# robinhood-cli/tests/unit/test_commands_market.py
from robinhood_core.models import Quote


def test_quote_to_row_positive_change():
    from robinhood_cli.commands.market import _quote_to_row
    q = Quote(
        symbol="AAPL",
        last_price=213.42,
        timestamp="2026-01-01T00:00:00Z",
        previous_close=211.58,
        change_percent=0.87,
    )
    row = _quote_to_row(q)
    assert row[0] == "AAPL"
    assert "$213.42" in row[1]


def test_quote_to_row_none_change():
    from robinhood_cli.commands.market import _quote_to_row
    q = Quote(
        symbol="TSLA",
        last_price=248.11,
        timestamp="2026-01-01T00:00:00Z",
    )
    row = _quote_to_row(q)
    assert row[0] == "TSLA"
```

**Step 2: Run to confirm failure**

```bash
uv run pytest tests/unit/test_commands_market.py -v
```

Expected: FAIL.

**Step 3: Implement `commands/market.py`**

```python
# robinhood-cli/robinhood_cli/commands/market.py
import asyncio
import json
from typing import Annotated, List, Optional

import typer
from rich.table import Table

from robinhood_core.services.market_data import MarketDataService
from robinhood_cli.auth import get_client
from robinhood_cli.output import (
    console,
    format_currency,
    format_change,
    format_percent,
    styled_change,
    print_json,
    POSITIVE,
    NEGATIVE,
    DIM,
)


def _quote_to_row(q) -> list:
    price = format_currency(q.last_price)
    change_val = None
    if q.previous_close is not None and q.last_price is not None:
        change_val = q.last_price - q.previous_close
    change_str = format_change(change_val)
    pct_str = format_percent(q.change_percent)
    return [q.symbol, price, change_str, pct_str, change_val]


def price_command(
    symbols: Annotated[List[str], typer.Argument(help="Ticker symbols")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = MarketDataService(client)
    quotes = svc.get_current_price(symbols)

    if json_output:
        print_json([q.model_dump() for q in quotes])
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Symbol")
    table.add_column("Price", justify="right")
    for q in quotes:
        table.add_row(q.symbol, format_currency(q.last_price))
    console.print(table)


def quote_command(
    symbols: Annotated[List[str], typer.Argument(help="Ticker symbols")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = MarketDataService(client)
    quotes = svc.get_current_price(symbols)

    if json_output:
        print_json([q.model_dump() for q in quotes])
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Symbol")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")

    for q in quotes:
        row = _quote_to_row(q)
        change_val = row[4]
        style = POSITIVE if (change_val or 0) >= 0 else NEGATIVE
        table.add_row(row[0], row[1], row[2], row[3], style=style)

    console.print(table)


def history_command(
    symbol: Annotated[str, typer.Argument(help="Ticker symbol")],
    interval: Annotated[str, typer.Option(help="5minute, 10minute, hour, day, week")] = "hour",
    span: Annotated[str, typer.Option(help="day, week, month, 3month, year, 5year")] = "week",
    bounds: Annotated[str, typer.Option(help="extended, trading, regular")] = "regular",
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = MarketDataService(client)
    candles = svc.get_price_history(symbol, interval, span, bounds)

    if json_output:
        print_json([c.model_dump() for c in candles])
        return

    table = Table(show_header=True, header_style="bold", title=f"{symbol} Price History")
    table.add_column("Timestamp")
    table.add_column("Open", justify="right")
    table.add_column("High", justify="right")
    table.add_column("Low", justify="right")
    table.add_column("Close", justify="right")
    table.add_column("Volume", justify="right")

    for c in candles:
        table.add_row(
            c.timestamp[:16].replace("T", " "),
            format_currency(c.open),
            format_currency(c.high),
            format_currency(c.low),
            format_currency(c.close),
            f"{c.volume:,}" if c.volume else "—",
        )
    console.print(table)


COMMANDS = [
    (price_command, "price", "Current prices for one or more symbols"),
    (quote_command, "quote", "Detailed quote with change and % change"),
    (history_command, "history", "Historical OHLCV price data"),
]
```

**Step 4: Run tests**

```bash
uv run pytest tests/unit/test_commands_market.py -v
```

Expected: All pass.

**Step 5: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add market commands (price, quote, history)"
```

---

### Task 11: Create portfolio commands — `rh portfolio`, `rh positions`

**TDD scenario:** New feature — write formatter tests first.

**Files:**
- Create: `robinhood-cli/robinhood_cli/commands/portfolio.py`
- Create: `robinhood-cli/tests/unit/test_commands_portfolio.py`

**Step 1: Write the failing test**

```python
# robinhood-cli/tests/unit/test_commands_portfolio.py
from robinhood_core.models import Position


def test_position_to_row():
    from robinhood_cli.commands.portfolio import _position_to_row
    p = Position(symbol="AAPL", quantity=10.0, average_cost=185.20, market_value=2134.20, unrealized_pl=490.00)
    row = _position_to_row(p)
    assert row[0] == "AAPL"
    assert "10" in row[1]
    assert "$185.20" in row[2]
    assert "+$490.00" in row[4] or "$490.00" in row[4]
```

**Step 2: Run to confirm failure**

```bash
uv run pytest tests/unit/test_commands_portfolio.py -v
```

**Step 3: Implement `commands/portfolio.py`**

```python
# robinhood-cli/robinhood_cli/commands/portfolio.py
from typing import Annotated, List, Optional

import typer
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from robinhood_core.services.portfolio import PortfolioService
from robinhood_cli.auth import get_client
from robinhood_cli.output import (
    console,
    format_currency,
    format_change,
    format_percent,
    styled_change,
    print_json,
    POSITIVE,
    NEGATIVE,
)


def _position_to_row(p) -> list:
    pl_str = format_change(p.unrealized_pl)
    return [
        p.symbol,
        f"{p.quantity:.4g}",
        format_currency(p.average_cost),
        format_currency(p.market_value),
        pl_str,
        p.unrealized_pl,
    ]


def portfolio_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = PortfolioService(client)
    summary = svc.get_portfolio_summary()

    if json_output:
        print_json(summary.model_dump())
        return

    day_change_str = format_change(summary.day_change)
    day_change_style = POSITIVE if (summary.day_change or 0) >= 0 else NEGATIVE

    lines = [
        f"[bold]Equity[/bold]        {format_currency(summary.equity)}",
        f"[bold]Cash[/bold]          {format_currency(summary.cash)}",
        f"[bold]Buying Power[/bold]  {format_currency(summary.buying_power)}",
        f"[bold]Day Change[/bold]    [{day_change_style}]{day_change_str}[/{day_change_style}]",
    ]
    console.print(Panel("\n".join(lines), title="Portfolio Summary", expand=False))


def positions_command(
    symbols: Annotated[Optional[List[str]], typer.Argument(help="Filter by symbols (optional)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = PortfolioService(client)
    positions = svc.get_positions(symbols)

    if json_output:
        print_json([p.model_dump() for p in positions])
        return

    if not positions:
        console.print("No open positions.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Symbol")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Market Value", justify="right")
    table.add_column("Unrealized P/L", justify="right")

    for p in positions:
        row = _position_to_row(p)
        pl_val = row[5]
        style = POSITIVE if (pl_val or 0) >= 0 else NEGATIVE
        table.add_row(row[0], row[1], row[2], row[3], row[4], style=style)

    console.print(table)


COMMANDS = [
    (portfolio_command, "portfolio", "Portfolio summary: equity, cash, buying power"),
    (positions_command, "positions", "Open stock positions"),
]
```

**Step 4: Run tests**

```bash
uv run pytest tests/unit/test_commands_portfolio.py -v
```

**Step 5: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add portfolio commands"
```

---

### Task 12: Create options commands — `rh options-chain`, `rh options-positions`

**TDD scenario:** New feature — write a formatter test first.

**Files:**
- Create: `robinhood-cli/robinhood_cli/commands/options.py`
- Create: `robinhood-cli/tests/unit/test_commands_options.py`

**Step 1: Write the failing test**

```python
# robinhood-cli/tests/unit/test_commands_options.py
from robinhood_core.models import OptionContract


def test_contract_to_row_basic():
    from robinhood_cli.commands.options import _contract_to_row
    c = OptionContract(symbol="AAPL", expiration="2026-06-20", strike=150.0, type="call")
    row = _contract_to_row(c)
    assert row[0] == "AAPL"
    assert "150" in row[2]
    assert row[3] == "call"
```

**Step 2: Run to confirm failure**

```bash
uv run pytest tests/unit/test_commands_options.py -v
```

**Step 3: Implement `commands/options.py`**

```python
# robinhood-cli/robinhood_cli/commands/options.py
from typing import Annotated, Optional

import typer
from rich.table import Table

from robinhood_core.services.options import OptionsService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, format_currency, format_percent, print_json, DIM


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
        console.print(f"[{DIM}]Tip: use --strike <price> to fetch full Greeks and bid/ask[/{DIM}]")


def options_positions_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
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
```

**Step 4: Run tests**

```bash
uv run pytest tests/unit/test_commands_options.py -v
```

**Step 5: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add options commands"
```

---

### Task 13: Create remaining commands — `rh watchlists`, `rh news`, `rh fundamentals`, `rh orders`

**TDD scenario:** New feature — write one formatter test per module.

**Files:**
- Create: `robinhood-cli/robinhood_cli/commands/watchlists.py`
- Create: `robinhood-cli/robinhood_cli/commands/news.py`
- Create: `robinhood-cli/robinhood_cli/commands/fundamentals.py`
- Create: `robinhood-cli/robinhood_cli/commands/orders.py`
- Create: `robinhood-cli/tests/unit/test_commands_remaining.py`

**Step 1: Write the failing tests**

```python
# robinhood-cli/tests/unit/test_commands_remaining.py
from robinhood_core.models import Watchlist, NewsItem, Fundamentals


def test_watchlist_symbols_joined():
    from robinhood_cli.commands.watchlists import _watchlist_to_rows
    w = Watchlist(id="1", name="Tech", symbols=["AAPL", "TSLA", "MSFT"])
    rows = _watchlist_to_rows(w)
    assert rows[0][0] == "Tech"
    symbols_str = rows[0][1]
    assert "AAPL" in symbols_str


def test_fundamentals_pe_formatted():
    from robinhood_cli.commands.fundamentals import _fundamentals_rows
    f = Fundamentals(market_cap=3_000_000_000_000.0, pe_ratio=32.5, dividend_yield=0.005, week_52_high=260.0, week_52_low=164.0)
    rows = _fundamentals_rows(f)
    labels = [r[0] for r in rows]
    assert "P/E Ratio" in labels
    assert "Market Cap" in labels
```

**Step 2: Run to confirm failure**

```bash
uv run pytest tests/unit/test_commands_remaining.py -v
```

**Step 3: Implement `commands/watchlists.py`**

```python
# robinhood-cli/robinhood_cli/commands/watchlists.py
from typing import Annotated
import typer
from rich.table import Table
from robinhood_core.services.watchlists import WatchlistsService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, print_json


def _watchlist_to_rows(w) -> list:
    return [[w.name, ", ".join(w.symbols)]]


def watchlists_command(
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = WatchlistsService(client)
    watchlists = svc.get_watchlists()

    if json_output:
        print_json([w.model_dump() for w in watchlists])
        return

    if not watchlists:
        console.print("No watchlists found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Symbols")

    for w in watchlists:
        for row in _watchlist_to_rows(w):
            table.add_row(*row)

    console.print(table)


COMMANDS = [
    (watchlists_command, "watchlists", "List all watchlists"),
]
```

**Step 4: Implement `commands/news.py`**

```python
# robinhood-cli/robinhood_cli/commands/news.py
import asyncio
from typing import Annotated
import typer
from rich.table import Table
from robinhood_core.services.news import NewsService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, print_json


def news_command(
    symbol: Annotated[str, typer.Argument(help="Ticker symbol")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    import asyncio
    client = get_client()
    svc = NewsService(client)
    news = asyncio.run(asyncio.to_thread(svc.get_news, symbol))

    if json_output:
        print_json([n.model_dump() for n in news])
        return

    if not news:
        console.print(f"No news found for {symbol}.")
        return

    table = Table(show_header=True, header_style="bold", title=f"{symbol} News")
    table.add_column("Published")
    table.add_column("Source")
    table.add_column("Headline")

    for n in news:
        published = n.published_at[:10] if n.published_at else "—"
        table.add_row(published, n.source or "—", n.headline)

    console.print(table)


COMMANDS = [
    (news_command, "news", "Latest news for a symbol"),
]
```

**Step 5: Implement `commands/fundamentals.py`**

```python
# robinhood-cli/robinhood_cli/commands/fundamentals.py
import asyncio
from typing import Annotated
import typer
from rich.table import Table
from robinhood_core.services.fundamentals import FundamentalsService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, format_currency, print_json


def _fundamentals_rows(f) -> list:
    def fmt_large(v):
        if v is None:
            return "—"
        if v >= 1_000_000_000_000:
            return f"${v / 1_000_000_000_000:.2f}T"
        if v >= 1_000_000_000:
            return f"${v / 1_000_000_000:.2f}B"
        if v >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        return format_currency(v)

    return [
        ["Market Cap", fmt_large(f.market_cap)],
        ["P/E Ratio", f"{f.pe_ratio:.2f}" if f.pe_ratio is not None else "—"],
        ["Dividend Yield", f"{f.dividend_yield:.2%}" if f.dividend_yield is not None else "—"],
        ["52-Week High", format_currency(f.week_52_high)],
        ["52-Week Low", format_currency(f.week_52_low)],
    ]


def fundamentals_command(
    symbol: Annotated[str, typer.Argument(help="Ticker symbol")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = FundamentalsService(client)
    f = asyncio.run(asyncio.to_thread(svc.get_fundamentals, symbol))

    if json_output:
        print_json(f.model_dump())
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold")
    table.add_column("Value", justify="right")

    for row in _fundamentals_rows(f):
        table.add_row(*row)

    from rich.panel import Panel
    console.print(Panel(table, title=f"{symbol} Fundamentals", expand=False))


COMMANDS = [
    (fundamentals_command, "fundamentals", "Company fundamentals (P/E, market cap, etc.)"),
]
```

**Step 6: Implement `commands/orders.py`**

```python
# robinhood-cli/robinhood_cli/commands/orders.py
import asyncio
from typing import Annotated, Optional
import typer
from rich.table import Table
from robinhood_core.services.orders import OrdersService
from robinhood_cli.auth import get_client
from robinhood_cli.output import console, format_currency, print_json, POSITIVE, NEGATIVE


def orders_command(
    order_type: Annotated[str, typer.Option("--type", help="stock, option, crypto, or all")] = "all",
    symbol: Annotated[Optional[str], typer.Option("--symbol", help="Filter by symbol")] = None,
    since: Annotated[Optional[str], typer.Option("--since", help="Start date YYYY-MM-DD")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    client = get_client()
    svc = OrdersService(client)
    history = asyncio.run(asyncio.to_thread(svc.get_order_history, order_type, symbol, since))

    if json_output:
        print_json(history.model_dump())
        return

    # Stock orders
    if history.stock_orders:
        table = Table(show_header=True, header_style="bold", title="Stock Orders")
        table.add_column("Date")
        table.add_column("Symbol")
        table.add_column("Side")
        table.add_column("State")
        table.add_column("Qty", justify="right")
        table.add_column("Avg Price", justify="right")

        for o in history.stock_orders:
            date = (o.created_at or "")[:10]
            side_style = POSITIVE if o.side == "buy" else NEGATIVE
            table.add_row(
                date,
                o.symbol or "—",
                f"[{side_style}]{o.side or '—'}[/{side_style}]",
                o.state or "—",
                f"{o.cumulative_quantity:.4g}" if o.cumulative_quantity else "—",
                format_currency(o.average_price),
            )
        console.print(table)

    # Option orders
    if history.option_orders:
        table = Table(show_header=True, header_style="bold", title="Option Orders")
        table.add_column("Date")
        table.add_column("Symbol")
        table.add_column("Direction")
        table.add_column("State")
        table.add_column("Qty", justify="right")
        table.add_column("Premium", justify="right")

        for o in history.option_orders:
            date = (o.created_at or "")[:10]
            table.add_row(
                date,
                o.chain_symbol or "—",
                o.direction or "—",
                o.state or "—",
                f"{o.processed_quantity:.4g}" if o.processed_quantity else "—",
                format_currency(o.processed_premium),
            )
        console.print(table)

    # Crypto orders
    if history.crypto_orders:
        table = Table(show_header=True, header_style="bold", title="Crypto Orders")
        table.add_column("Date")
        table.add_column("Side")
        table.add_column("State")
        table.add_column("Qty", justify="right")
        table.add_column("Avg Price", justify="right")

        for o in history.crypto_orders:
            date = (o.created_at or "")[:10]
            side_style = POSITIVE if o.side == "buy" else NEGATIVE
            table.add_row(
                date,
                f"[{side_style}]{o.side or '—'}[/{side_style}]",
                o.state or "—",
                f"{o.cumulative_quantity:.4g}" if o.cumulative_quantity else "—",
                format_currency(o.average_price),
            )
        console.print(table)

    total = len(history.stock_orders) + len(history.option_orders) + len(history.crypto_orders)
    if total == 0:
        console.print("No orders found.")


COMMANDS = [
    (orders_command, "orders", "Order history (stock, option, crypto)"),
]
```

**Step 7: Run all remaining tests**

```bash
uv run pytest tests/unit/test_commands_remaining.py -v
```

Expected: All pass.

**Step 8: Commit**

```bash
git add robinhood-cli/
git commit -m "feat(cli): add watchlists, news, fundamentals, orders commands"
```

---

### Task 14: Smoke-test the full CLI

**TDD scenario:** Integration verification — not a unit test; just confirm `rh --help` lists all commands.

**Step 1: Verify help output**

```bash
cd robinhood-cli
uv run rh --help
```

Expected output lists all commands:
```
login, logout, status, price, quote, history, portfolio, positions,
options-chain, options-positions, watchlists, news, fundamentals, orders
```

**Step 2: Run full CLI test suite**

```bash
uv run pytest tests/ -v
```

Expected: All pass.

**Step 3: Commit**

```bash
git add robinhood-cli/
git commit -m "test(cli): verify full command registration"
```

---

### Task 15: Rewrite root `README.md`

**TDD scenario:** Trivial doc update — no tests.

**Files:**
- Modify: `README.md` (repo root at `robinhood-mcp/README.md`)

**Step 1: Rewrite the README**

The README must cover:
1. **Monorepo overview** — three packages, one repo
2. **`robinhood-core`** — what it is (internal library, not a user-facing tool)
3. **`robinhood-cli` quickstart** — `uv pip install -e robinhood-cli`, `rh login`, example commands with sample output
4. **`robinhood-mcp` quickstart** — `uv pip install -e robinhood-mcp`, Claude Desktop config JSON
5. **Auth** — how `rh login` works, how the MCP uses env vars
6. **Available commands** — table of all `rh` subcommands

Structure:
```markdown
# Robinhood Tools

A monorepo with two Robinhood tools built on a shared core:

- **`rh`** — CLI for terminal use
- **`robinhood-mcp`** — MCP server for AI assistants (Claude, Cursor, etc.)

## Packages

| Package | Purpose |
|---|---|
| `robinhood-core` | Shared models, services, and auth client |
| `robinhood-cli` | `rh` CLI tool |
| `robinhood-mcp` | MCP server |

## CLI (`rh`) Quickstart

...install, login, example commands...

## MCP Server Quickstart

...install, Claude Desktop config...

## Authentication

...rh login flow, env vars for MCP...

## Commands

| Command | Description |
|---|---|
| `rh login` | ... |
...
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite root README for monorepo with CLI and MCP"
```

---

## ✅ Phase 2 Complete

Run final verification across all three packages:

```bash
cd robinhood-core && uv run pytest tests/ -v
cd ../robinhood-mcp && uv run pytest tests/ -v
cd ../robinhood-cli && uv run pytest tests/ -v
```

All three suites must be green before marking done.
