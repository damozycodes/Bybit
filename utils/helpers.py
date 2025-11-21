"""
Helper utility functions (continued)
"""
import time
import functools
from typing import Any, Callable, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference
    
    Args:
        dt: datetime object
    
    Returns:
        Human-readable time string (e.g., "5 minutes ago")
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def calculate_roi(entry_price: float, exit_price: float, 
                  side: str, leverage: int = 1) -> float:
    """
    Calculate ROI percentage
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        side: 'long' or 'short'
        leverage: Leverage multiplier
    
    Returns:
        ROI percentage
    """
    if entry_price <= 0:
        return 0.0
    
    if side.lower() == 'long':
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
    else:  # short
        pnl_percent = ((entry_price - exit_price) / entry_price) * 100
    
    return pnl_percent * leverage


def calculate_liquidation_price(entry_price: float, side: str, 
                                leverage: int, maintenance_margin: float = 0.5) -> float:
    """
    Estimate liquidation price
    
    Args:
        entry_price: Entry price
        side: 'long' or 'short'
        leverage: Leverage multiplier
        maintenance_margin: Maintenance margin percentage
    
    Returns:
        Estimated liquidation price
    """
    margin_ratio = (100 - maintenance_margin) / 100
    
    if side.lower() == 'long':
        liq_price = entry_price * (1 - margin_ratio / leverage)
    else:  # short
        liq_price = entry_price * (1 + margin_ratio / leverage)
    
    return liq_price


def truncate_address(address: str, chars: int = 8) -> str:
    """
    Truncate wallet address for display
    
    Args:
        address: Full wallet address
        chars: Number of characters to show on each end
    
    Returns:
        Truncated address (e.g., "0x1234...5678")
    """
    if not address or len(address) <= chars * 2:
        return address
    
    return f"{address[:chars]}...{address[-chars:]}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that returns default on zero division
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
    
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def round_to_precision(value: float, precision: int) -> float:
    """
    Round value to specific decimal precision
    
    Args:
        value: Value to round
        precision: Number of decimal places
    
    Returns:
        Rounded value
    """
    multiplier = 10 ** precision
    return round(value * multiplier) / multiplier


def parse_symbol(symbol: str) -> tuple:
    """
    Parse trading symbol into base and quote currencies
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
    
    Returns:
        Tuple of (base_currency, quote_currency)
    """
    if '/' in symbol:
        parts = symbol.split('/')
        return parts[0], parts[1]
    return symbol, 'USDT'


def is_market_open() -> bool:
    """
    Check if crypto market is open (always true for crypto)
    
    Returns:
        True (crypto markets are 24/7)
    """
    return True


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls allowed in period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def can_call(self) -> bool:
        """Check if a call can be made"""
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        return len(self.calls) < self.max_calls
    
    def add_call(self):
        """Record a call"""
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        while not self.can_call():
            time.sleep(0.1)
        self.add_call()