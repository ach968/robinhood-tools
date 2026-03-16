# tests/unit/test_service_fundamentals.py
import pytest
from unittest.mock import MagicMock, patch
from robinhood_core.services.fundamentals import FundamentalsService
from robinhood_core.client import RobinhoodClient
from robinhood_core.errors import InvalidArgumentError, RobinhoodAPIError


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)
    assert service.client == mock_client


def test_get_fundamentals_requires_symbol():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    with pytest.raises(InvalidArgumentError, match="Symbol is required"):
        service.get_fundamentals("")


def test_get_fundamentals_success():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    mock_fundamentals_data = {
        "market_cap": "2500000000000.0",
        "pe_ratio": "28.5",
        "dividend_yield": "0.005",
        "high_52_weeks": "200.0",
        "low_52_weeks": "140.0",
    }

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.return_value = [mock_fundamentals_data]

        fundamentals = service.get_fundamentals("AAPL")

        assert fundamentals.market_cap == 2500000000000.0
        assert fundamentals.pe_ratio == 28.5
        assert fundamentals.dividend_yield == 0.005
        assert fundamentals.week_52_high == 200.0
        assert fundamentals.week_52_low == 140.0

        mock_rh.get_fundamentals.assert_called_once_with("AAPL")


def test_get_fundamentals_single_dict_response():
    """Test when API returns a single dict instead of list."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    mock_fundamentals_data = {
        "market_cap": "1000000000.0",
        "pe_ratio": "15.5",
        "dividend_yield": None,
        "high_52_weeks": "150.0",
        "low_52_weeks": "100.0",
    }

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.return_value = mock_fundamentals_data

        fundamentals = service.get_fundamentals("TSLA")

        assert fundamentals.market_cap == 1000000000.0
        assert fundamentals.pe_ratio == 15.5
        assert fundamentals.dividend_yield is None
        assert fundamentals.week_52_high == 150.0
        assert fundamentals.week_52_low == 100.0


def test_get_fundamentals_empty_response():
    """Test when API returns empty list - returns empty Fundamentals object."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.return_value = []

        fundamentals = service.get_fundamentals("INVALID")

        assert fundamentals.market_cap is None
        assert fundamentals.pe_ratio is None
        assert fundamentals.dividend_yield is None
        assert fundamentals.week_52_high is None
        assert fundamentals.week_52_low is None


def test_get_fundamentals_api_error():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.side_effect = Exception("API Error")

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch fundamentals"):
            service.get_fundamentals("AAPL")


def test_get_fundamentals_calls_ensure_session():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.return_value = [{"market_cap": "1000.0"}]

        service.get_fundamentals("AAPL")

        mock_client.ensure_session.assert_called_once()


def test_get_fundamentals_with_string_values():
    """Test that string values from API are properly coerced to floats."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)

    mock_fundamentals_data = {
        "market_cap": "1234567890",
        "pe_ratio": "25",
        "dividend_yield": "0.025",
        "high_52_weeks": "300.50",
        "low_52_weeks": "200.25",
    }

    with patch("robinhood_core.services.fundamentals.rh") as mock_rh:
        mock_rh.get_fundamentals.return_value = [mock_fundamentals_data]

        fundamentals = service.get_fundamentals("MSFT")

        assert isinstance(fundamentals.market_cap, float)
        assert isinstance(fundamentals.pe_ratio, float)
        assert isinstance(fundamentals.dividend_yield, float)
        assert isinstance(fundamentals.week_52_high, float)
        assert isinstance(fundamentals.week_52_low, float)
