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
    import click
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        get_client(session_dir=tmp_path)
