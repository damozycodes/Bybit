import time
from typing import Optional
from core.exchange_client import ExchangeClient
from utils.logger import get_logger
from config.settings import (
    AUTO_WITHDRAW_ENABLED, 
    WITHDRAWAL_ADDRESS, 
    WITHDRAWAL_NETWORK,
    MIN_WITHDRAWAL_AMOUNT
)

logger = get_logger(__name__)


class WithdrawalManager:
    """Manage cryptocurrency withdrawals"""
    
    def __init__(self, exchange_client: ExchangeClient):
        self.exchange = exchange_client
        self.auto_withdraw_enabled = AUTO_WITHDRAW_ENABLED
        self.withdrawal_address = WITHDRAWAL_ADDRESS
        self.withdrawal_network = WITHDRAWAL_NETWORK
        self.min_amount = MIN_WITHDRAWAL_AMOUNT
    
    def execute_withdrawal(self, asset: str, amount: Optional[float] = None) -> Optional[dict]:
        """
        Execute cryptocurrency withdrawal
        
        Args:
            asset: Cryptocurrency to withdraw
            amount: Amount to withdraw (None = all available)
        
        Returns:
            Withdrawal result or None
        """
        if not self.auto_withdraw_enabled:
            logger.info("Auto-withdrawal is disabled")
            return None
        
        if not self.withdrawal_address:
            logger.error("Withdrawal address not configured")
            return None
        
        try:
            # Get available balance
            balance = self.exchange.get_account_balance()
            available = float(balance.get('free', {}).get(asset, 0))
            
            # Use all available if amount not specified
            if amount is None:
                amount = available
            
            # Check minimum amount
            if amount < self.min_amount:
                logger.warning(f"Amount {amount} below minimum {self.min_amount}")
                return None
            
            if available < amount:
                logger.warning(f"Insufficient {asset} balance for withdrawal")
                return None
            
            logger.info(f"Withdrawing {amount} {asset} to {self.withdrawal_address}")
            
            # Execute withdrawal
            result = self.exchange.withdraw_crypto(
                asset=asset,
                amount=amount,
                address=self.withdrawal_address,
                network=self.withdrawal_network
            )
            
            logger.info(f"Withdrawal successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Withdrawal failed: {str(e)}")
            return None
    
    def auto_withdraw_after_conversion(self, asset: str, 
                                      wait_seconds: int = 10) -> Optional[dict]:
        """
        Automatically withdraw after conversion
        
        Args:
            asset: Cryptocurrency to withdraw
            wait_seconds: Seconds to wait before withdrawal
        
        Returns:
            Withdrawal result or None
        """
        if not self.auto_withdraw_enabled:
            return None
        
        try:
            # Wait for conversion settlement
            logger.info(f"Waiting {wait_seconds}s for conversion settlement...")
            time.sleep(wait_seconds)
            
            # Execute withdrawal
            return self.execute_withdrawal(asset)
            
        except Exception as e:
            logger.error(f"Auto-withdrawal after conversion failed: {str(e)}")
            return None
    
    def check_funds_available(self, asset: str, required_amount: float) -> bool:
        """
        Check if sufficient funds are available
        
        Args:
            asset: Cryptocurrency symbol
            required_amount: Required amount
        
        Returns:
            True if sufficient funds available
        """
        try:
            balance = self.exchange.get_account_balance()
            available = float(balance.get('free', {}).get(asset, 0))
            return available >= required_amount
        except Exception as e:
            logger.error(f"Failed to check funds: {str(e)}")
            return False