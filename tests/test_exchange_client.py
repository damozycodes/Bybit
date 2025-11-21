import pytest
from unittest.mock import patch, MagicMock
from core.exchange_client import ExchangeClient


@pytest.fixture
def mock_ccxt():
    """Patch CCXT globally for all tests."""
    with patch("core.exchange_client.ccxt") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    with patch("core.exchange_client.logger") as mock:
        yield mock


@pytest.fixture
def client(mock_ccxt, mock_logger):
    """
    Create a test ExchangeClient instance with CCXT mocked.
    """
    # Configure exchange mock
    mock_exchange_class = MagicMock()
    mock_exchange_instance = MagicMock()

    # ccxt.bybit → returns mock instance
    mock_ccxt.bybit = mock_exchange_class
    mock_exchange_class.return_value = mock_exchange_instance

    # Required CCXT return values for initialization
    mock_exchange_instance.load_markets.return_value = {}

    # Create client
    c = ExchangeClient()

    # Override exchange instance for ease of access
    c.exchange = mock_exchange_instance

    return c


# ---------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------

def test_initialize_exchange(client, mock_ccxt):
    assert hasattr(client, "exchange")


def test_get_account_balance(client):
    client.exchange.fetch_balance.return_value = {"USDT": {"free": 100}}
    balance = client.get_account_balance()
    assert balance["USDT"]["free"] == 100


def test_get_open_positions(client):
    mock_positions = [
        {"symbol": "BTC/USDT", "contracts": 0.01},
        {"symbol": "ETH/USDT", "contracts": 0.0}
    ]
    client.exchange.fetch_positions.return_value = mock_positions

    result = client.get_open_positions()
    assert len(result) == 1
    assert result[0]["symbol"] == "BTC/USDT"


def test_get_position_by_symbol(client):
    mock_positions = [
        {"symbol": "BTC/USDT", "contracts": 0.01},
    ]
    client.exchange.fetch_positions.return_value = mock_positions
    pos = client.get_position_by_symbol("BTC/USDT")
    assert pos is not None
    assert pos["symbol"] == "BTC/USDT"


def test_calculate_position_pnl(client):
    position = {
        "symbol": "BTC/USDT",
        "entryPrice": "50000",
        "contracts": "0.01",
        "side": "long"
    }

    client.exchange.fetch_ticker.return_value = {"last": 50500}

    pnl = client.calculate_position_pnl(position)
    assert pnl == (50500 - 50000) * 0.01


def test_create_market_order(client):
    client.exchange.create_order.return_value = {"id": "order123"}

    order = client.create_market_order(
        symbol="BTC/USDT",
        side="buy",
        amount=0.01
    )

    assert order["id"] == "order123"
    client.exchange.create_order.assert_called_once()


def test_close_position(client):
    # Mock open position
    mock_pos = {
        "symbol": "BTC/USDT",
        "contracts": 0.01,
        "side": "long"
    }

    client.exchange.fetch_positions.return_value = [mock_pos]
    client.exchange.create_order.return_value = {"id": "close123"}

    order = client.close_position("BTC/USDT", "long")

    assert order["id"] == "close123"
    client.exchange.create_order.assert_called_once()


def test_convert_crypto(client):
    client.exchange.sapi_post_convert_getquote.return_value = {"quoteId": "abc123"}
    client.exchange.sapi_post_convert_acceptquote.return_value = {"executed": True}

    result = client.convert_crypto("BTC", "USDT", 0.01)

    assert result["executed"] is True
    client.exchange.sapi_post_convert_acceptquote.assert_called_once()


def test_withdraw_crypto(client):
    client.exchange.withdraw.return_value = {"id": "wd123"}

    result = client.withdraw_crypto("USDT", 50, "wallet_address", "TRC20")

    assert result["id"] == "wd123"
    client.exchange.withdraw.assert_called_once()


def test_set_leverage(client):
    client.set_leverage("BTC/USDT", 20)
    client.exchange.set_leverage.assert_called_once_with(20, "BTC/USDT")


def test_set_margin_mode(client):
    client.set_margin_mode("BTC/USDT", "isolated")
    client.exchange.set_margin_mode.assert_called_once_with("isolated", "BTC/USDT")
