from typing import Dict, Optional
from core.exchange_client import ExchangeClient
from utils.logger import get_logger
from utils.exceptions import OrderExecutionError

logger = get_logger(__name__)


class OrderExecutor:
    """Handle order execution and position management"""
    
    def __init__(self, exchange_client: ExchangeClient):
        self.exchange = exchange_client
    
    def open_position(self, symbol: str, side: str, quantity: float,
                     leverage: int = 10, margin_mode: str = 'isolated') -> Dict:
        """
        Open a new position
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'long' or 'short'/ 'buy' or 'sell'
            quantity: Position size
            leverage: Leverage multiplier
            margin_mode: 'isolated' or 'cross'
        
        Returns:
            Order details
        """
        try:
            # Set leverage and margin mode
            self.exchange.set_leverage(symbol, leverage)
            self.exchange.set_margin_mode(symbol, margin_mode)
            
            # Determine order side
            order_side = 'buy' if side == 'long' else 'sell'
            
            # Create market order
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=order_side,
                amount=quantity
            )
            
            logger.info(f"Position opened: {side} {quantity} {symbol} at {leverage}x leverage")
            return order
            
        except Exception as e:
            logger.error(f"Failed to open position: {str(e)}")
            raise OrderExecutionError(f"Position opening failed: {str(e)}")
    
    def close_position(self, symbol: str, position_side: str) -> Dict:
        """
        Close an existing position
        
        Args:
            symbol: Trading pair
            position_side: 'long' or 'short'
        
        Returns:
            Order details
        """
        try:
            order = self.exchange.close_position(symbol, position_side)
            
            if order:
                logger.info(f"Position closed successfully for {symbol}")
            else:
                logger.warning(f"No position to close for {symbol}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            raise OrderExecutionError(f"Position closure failed: {str(e)}")
    
    def execute_profit_close(self, position: Dict, profit: float) -> Dict:
        """
        Close position when profit threshold is reached
        
        Args:
            position: Position details
            profit: Realized profit amount
        
        Returns:
            Order details
        """
        try:
            symbol = position['symbol']
            side = position['side']
            
            logger.info(f"Executing profit close for {symbol} with profit ${profit:.2f}")
            
            order = self.close_position(symbol, side)
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to execute profit close: {str(e)}")
            raise OrderExecutionError(f"Profit close failed: {str(e)}")