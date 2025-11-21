import pytest
from core.exchange_client import ExchangeClient
from core.order_executor import OrderExecutor
from utils.exceptions import OrderExecutionError
import time

# -----------------------------
# MARK AS INTEGRATION TEST
# -----------------------------
pytestmark = pytest.mark.integration

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture(scope="module")
def exchange_client():
    """Real ExchangeClient connected to Bybit testnet"""
    client = ExchangeClient()
    return client


@pytest.fixture(scope="module")
def executor(exchange_client):
    """OrderExecutor using the real exchange client"""
    return OrderExecutor(exchange_client)


# -----------------------------
# TESTS
# -----------------------------

def test_open_and_close_position(executor):
    """Test opening and closing a small position on testnet"""
    symbol = "BTC/USDT"
    quantity = 0.001  # Small amount for testnet
    side = "long"

    # Open position
    order = executor.open_position(symbol, side, quantity, leverage=5, margin_mode="isolated")
    assert order is not None
    assert "id" in order
    print(f"Opened test position: {order['id']}")

    # Optional: wait a few seconds for the order to settle
    time.sleep(2)

    # Close position
    close_order = executor.close_position(symbol, side)
    assert close_order is not None
    assert "id" in close_order
    print(f"Closed test position: {close_order['id']}")


def test_execute_profit_close(executor):
    """Simulate profit-close flow on testnet"""
    symbol = "BTC/USDT"
    quantity = 0.001

    # Open a position first
    position_order = executor.open_position(symbol, "long", quantity)
    position = {
        "symbol": symbol,
        "side": "long",
        "contracts": quantity,
        "entryPrice": 50000  # Just a placeholder
    }

    # Simulate hitting a profit target
    profit = 10.0  # USD
    result = executor.execute_profit_close(position, profit)
    assert result is not None
    assert "id" in result
    print(f"Profit close executed: {result['id']}")
