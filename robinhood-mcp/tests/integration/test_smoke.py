# tests/integration/test_smoke.py
import pytest
import os

# Skip if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("RH_INTEGRATION"),
    reason="Integration tests disabled. Set RH_INTEGRATION=1 to run.",
)


def test_client_can_load():
    """Verify client can be imported and initialized."""
    from robinhood_core.client import RobinhoodClient

    client = RobinhoodClient()
    assert client is not None


def test_server_can_import():
    """Verify server module can be imported."""
    from robin_stocks_mcp.server import mcp

    assert mcp is not None
