"""
Logging configuration and utilities
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_FILE, MAX_LOG_SIZE, BACKUP_COUNT


def setup_logger():
    """Setup application-wide logging configuration"""
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TradeLogger:
    """Specialized logger for trade events"""
    
    def __init__(self):
        self.logger = get_logger('trades')
        self.trade_log_file = 'logs/trades.log'
        self._setup_trade_logger()
    
    def _setup_trade_logger(self):
        """Setup dedicated trade log file"""
        log_dir = os.path.dirname(self.trade_log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler = RotatingFileHandler(
            self.trade_log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_position_opened(self, symbol: str, side: str, quantity: float, 
                           entry_price: float, leverage: int):
        """Log position opened event"""
        self.logger.info(
            f"POSITION_OPENED | {symbol} | {side.upper()} | "
            f"Qty: {quantity} | Entry: ${entry_price:.2f} | Leverage: {leverage}x"
        )
    
    def log_position_closed(self, symbol: str, side: str, entry_price: float,
                           exit_price: float, profit: float):
        """Log position closed event"""
        profit_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
        self.logger.info(
            f"POSITION_CLOSED | {symbol} | {side.upper()} | "
            f"Entry: ${entry_price:.2f} | Exit: ${exit_price:.2f} | P/L: {profit_str}"
        )
    
    def log_conversion(self, from_asset: str, to_asset: str, 
                      from_amount: float, to_amount: float):
        """Log conversion event"""
        self.logger.info(
            f"CONVERSION | {from_amount} {from_asset} -> {to_amount} {to_asset}"
        )
    
    def log_withdrawal(self, asset: str, amount: float, address: str, tx_id: str):
        """Log withdrawal event"""
        self.logger.info(
            f"WITHDRAWAL | {amount} {asset} | To: {address[:20]}... | TX: {tx_id}"
        )
    
    def log_liquidation(self, balance: float, expected: float):
        """Log liquidation event"""
        self.logger.critical(
            f"LIQUIDATION | Balance: ${balance:.2f} | Expected: ${expected:.2f} | "
            f"Loss: ${expected - balance:.2f}"
        )


# Initialize logger on import
setup_logger()