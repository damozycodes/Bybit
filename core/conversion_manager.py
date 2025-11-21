import time
from typing import Optional
from core.exchange_client import ExchangeClient
from utils.logger import get_logger
from config.settings import CONVERT_TO_CRYPTO, AUTO_CONVERT_ENABLED

logger = get_logger(__name__)


class ConversionManager:
    """Manage cryptocurrency conversions"""
    
    def __init__(self, exchange_client: ExchangeClient):
        self.exchange = exchange_client
        self.auto_convert_enabled = AUTO_CONVERT_ENABLED
        self.target_crypto = CONVERT_TO_CRYPTO
    
    def execute_conversion(self, from_asset: str, amount: float, 
                          to_asset: Optional[str] = None) -> Optional[dict]:
        """
        Execute cryptocurrency conversion
        
        Args:
            from_asset: Source cryptocurrency
            amount: Amount to convert
            to_asset: Target cryptocurrency (defaults to config)
        
        Returns:
            Conversion result or None
        """
        if not self.auto_convert_enabled:
            logger.info("Auto-conversion is disabled")
            return None
        
        if to_asset is None:
            to_asset = self.target_crypto
        
        try:
            # Check if we have enough balance
            balance = self.exchange.get_account_balance()
            available = float(balance.get('free', {}).get(from_asset, 0))
            
            if available < amount:
                logger.warning(f"Insufficient {from_asset} balance for conversion")
                return None
            
            logger.info(f"Converting {amount} {from_asset} to {to_asset}")
            
            # Execute conversion
            result = self.exchange.convert_crypto(from_asset, to_asset, amount)
            
            logger.info(f"Conversion successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            return None
    
    def auto_convert_after_close(self, closed_position: dict, 
                                 wait_seconds: int = 5) -> Optional[dict]:
        """
        Automatically convert after position closure
        
        Args:
            closed_position: Details of closed position
            wait_seconds: Seconds to wait before conversion
        
        Returns:
            Conversion result or None
        """
        if not self.auto_convert_enabled:
            return None
        
        try:
            # Wait for settlement
            logger.info(f"Waiting {wait_seconds}s for position settlement...")
            time.sleep(wait_seconds)
            
            # Extract base asset from symbol (e.g., 'BTC' from 'BTC/USDT')
            symbol = closed_position.get('symbol', '')
            base_asset = symbol.split('/')[0] if '/' in symbol else 'BTC'
            
            # Get available balance
            balance = self.exchange.get_account_balance()
            available_amount = float(balance.get('free', {}).get(base_asset, 0))
            
            if available_amount <= 0:
                logger.warning(f"No {base_asset} available for conversion")
                return None
            
            # Execute conversion
            return self.execute_conversion(base_asset, available_amount)
            
        except Exception as e:
            logger.error(f"Auto-conversion after close failed: {str(e)}")
            return None