"""
Position monitoring and profit tracking
"""
import time
import threading
from typing import Callable, Optional
from core.exchange_client import ExchangeClient
from utils.logger import get_logger
from config.settings import MONITOR_INTERVAL

logger = get_logger(__name__)


class PositionMonitor:
    """Monitor positions and trigger actions based on profit thresholds"""
    
    def __init__(self, exchange_client: ExchangeClient):
        self.exchange = exchange_client
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.profit_threshold = 0  # USD
        self.monitored_symbol: Optional[str] = None
        self.on_profit_reached: Optional[Callable] = None
        
    def start_monitoring(self, symbol: str, profit_threshold: float, 
                        on_profit_reached: Callable):
        """
        Start monitoring a position
        
        Args:
            symbol: Trading pair to monitor
            profit_threshold: Profit in USD to trigger action
            on_profit_reached: Callback function when profit is reached
        """
        if self.monitoring:
            logger.warning("Monitor already running")
            return
        
        self.monitored_symbol = symbol
        self.profit_threshold = profit_threshold
        self.on_profit_reached = on_profit_reached
        self.monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Started monitoring {symbol} with profit threshold ${profit_threshold}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Stopped position monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                position = self.exchange.get_position_by_symbol(self.monitored_symbol)
                
                if not position:
                    logger.warning(f"No position found for {self.monitored_symbol}")
                    time.sleep(MONITOR_INTERVAL)
                    continue
                
                # Calculate current PnL
                current_pnl = self.exchange.calculate_position_pnl(position)
                
                logger.debug(f"Current PnL for {self.monitored_symbol}: ${current_pnl:.2f}")
                
                # Check if profit threshold reached
                if current_pnl >= self.profit_threshold:
                    logger.info(f"Profit threshold reached! PnL: ${current_pnl:.2f}")
                    self.monitoring = False  # Stop monitoring before callback
                    
                    # Trigger callback
                    if self.on_profit_reached:
                        self.on_profit_reached(position, current_pnl)
                    break
                
                time.sleep(MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(MONITOR_INTERVAL)
    
    def get_current_pnl(self, symbol: str) -> float:
        """Get current PnL for a position"""
        try:
            position = self.exchange.get_position_by_symbol(symbol)
            if position:
                return self.exchange.calculate_position_pnl(position)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get PnL: {str(e)}")
            return 0.0
    
    def check_liquidation(self) -> bool:
        """
        Check if account has been liquidated
        Returns True if liquidation detected
        """
        try:
            balance = self.exchange.get_account_balance()
            positions = self.exchange.get_open_positions()
            
            # Get total equity
            total_equity = float(balance.get('total', {}).get('USDT', 0))
            
            # If equity is very low and no open positions, likely liquidated
            if total_equity < 1.0 and len(positions) == 0:
                logger.error("Liquidation detected!")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check liquidation: {str(e)}")
            return False