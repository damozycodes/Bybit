import pytest
from unittest.mock import MagicMock
from core.order_executor import OrderExecutor
from utils.exceptions import OrderExecutionError


@pytest.fixture
def mock_exchange():
    """Mock exchange client for testing."""
    exchange = MagicMock()
    exchange.set_leverage.return_value = None
    exchange.set_margin_mode.return_value = None
    return exchange


@pytest.fixture
def executor(mock_exchange):
    """OrderExecutor instance using mocked exchange."""
    return OrderExecutor(mock_exchange)


# -------------------------------
# OPEN POSITION
# -------------------------------
def test_open_position_long(executor, mock_exchange):
    mock_exchange.create_market_order.return_value = {"order_id": "1"}

    result = executor.open_position(
        symbol="BTC/USDT",
        side="long",
        quantity=0.01,
        leverage=10,
        margin_mode="isolated",
    )

    # Assertions
    mock_exchange.set_leverage.assert_called_once_with("BTC/USDT", 10)
    mock_exchange.set_margin_mode.assert_called_once_with("BTC/USDT", "isolated")
    mock_exchange.create_market_order.assert_called_once_with(
        symbol="BTC/USDT",
        side="buy",
        amount=0.01,
    )
    assert result == {"order_id": "1"}


def test_open_position_short(executor, mock_exchange):
    mock_exchange.create_market_order.return_value = {"order_id": "2"}

    result = executor.open_position(
        symbol="ETH/USDT",
        side="short",
        quantity=1,
        leverage=5,
        margin_mode="cross",
    )

    mock_exchange.create_market_order.assert_called_once_with(
        symbol="ETH/USDT",
        side="sell",
        amount=1,
    )
    assert result == {"order_id": "2"}


def test_open_position_failure(executor, mock_exchange):
    mock_exchange.create_market_order.side_effect = Exception("API ERROR")

    with pytest.raises(OrderExecutionError):
        executor.open_position("BTC/USDT", "long", 0.01)


# -------------------------------
# CLOSE POSITION
# -------------------------------
def test_close_position_success(executor, mock_exchange):
    mock_exchange.close_position.return_value = {"closed": True}

    result = executor.close_position("BTC/USDT", "long")

    mock_exchange.close_position.assert_called_once_with("BTC/USDT", "long")
    assert result == {"closed": True}


def test_close_position_no_position(executor, mock_exchange):
    mock_exchange.close_position.return_value = None

    result = executor.close_position("BTC/USDT", "long")

    assert result is None


def test_close_position_failure(executor, mock_exchange):
    mock_exchange.close_position.side_effect = Exception("Close failed")

    with pytest.raises(OrderExecutionError):
        executor.close_position("BTC/USDT", "short")


# -------------------------------
# EXECUTE PROFIT CLOSE
# -------------------------------
def test_execute_profit_close_success(executor, mock_exchange):
    mock_exchange.close_position.return_value = {"closed": True}

    position = {"symbol": "BTC/USDT", "side": "long"}

    result = executor.execute_profit_close(position, profit=50.0)

    mock_exchange.close_position.assert_called_once_with("BTC/USDT", "long")
    assert result == {"closed": True}


def test_execute_profit_close_failure(executor, mock_exchange):
    mock_exchange.close_position.side_effect = Exception("Error")

    position = {"symbol": "BTC/USDT", "side": "short"}

    with pytest.raises(OrderExecutionError):
        executor.execute_profit_close(position, profit=100.0)
