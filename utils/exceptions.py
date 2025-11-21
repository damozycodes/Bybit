class ExchangeError(Exception):
    """Base class for exchange-related errors."""
    pass

class InsufficientFundsError(ExchangeError):
    """Raised when an account has insufficient funds for an operation."""
    pass

class OrderExecutionError(ExchangeError):
    """Raised when an order fails to execute or is rejected by the broker/exchange."""

    def __init__(self, message: str = "Order execution failed", *args, **kwargs):
        super().__init__(message)