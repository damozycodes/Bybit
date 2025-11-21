
import ccxt
import time
import hmac
import hashlib
from typing import Dict, List, Optional
from config.settings import API_KEY, API_SECRET, EXCHANGE_NAME, TESTNET
from config.api_config import get_exchange_config
from utils.logger import get_logger
from utils.exceptions import ExchangeError, InsufficientFundsError


logger = get_logger(__name__)


class ExchangeClient:
    """Wrapper for exchange API operations"""
    
    def __init__(self):
        self.exchange_name = EXCHANGE_NAME
        self.testnet = TESTNET
        self.config = get_exchange_config(EXCHANGE_NAME, TESTNET)
        self.exchange = self._initialize_exchange()
        
    def _initialize_exchange(self):
        try:
            exchange_class = getattr(ccxt, self.exchange_name)

            exchange = exchange_class({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'enableRateLimit': True
            })

            # Use correct testnet endpoint for v5
            if self.testnet:
                exchange.set_sandbox_mode(True)
            
            exchange.options['defaultType'] = 'future'
            markets = exchange.load_markets()

            logger.info(f"Successfully connected to {self.exchange_name}")
            return exchange

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {str(e)}")
            return None
        
        
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            print(balance)
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {str(e)}")
            raise ExchangeError(f"Balance fetch failed: {str(e)}")

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        try:
            positions = self.exchange.fetch_positions()
            # Filter only positions with non-zero size
            open_positions = [
                pos for pos in positions 
                if float(pos.get('contracts', 0)) > 0
            ]
            return open_positions
        except Exception as e:
            logger.error(f"Failed to fetch positions: {str(e)}")
            raise ExchangeError(f"Position fetch failed: {str(e)}")
    
    def get_position_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get specific position by symbol"""
        try:
            positions = self.get_open_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    return pos
            return None
        except Exception as e:
            logger.error(f"Failed to get position for {symbol}: {str(e)}")
            return None
    
    def calculate_position_pnl(self, position: Dict) -> float:
        """Calculate unrealized PnL for a position"""
        try:
            # Get current market price
            symbol = position['symbol']
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Calculate PnL
            entry_price = float(position['entryPrice'])
            contracts = float(position['contracts'])
            side = position['side']  # 'long' or 'short'
            
            if side == 'long':
                pnl = (current_price - entry_price) * contracts
            else:  # short
                pnl = (entry_price - current_price) * contracts
            
            return pnl
            
        except Exception as e:
            logger.error(f"Failed to calculate PnL: {str(e)}")
            return 0.0
    
    def create_market_order(self, symbol: str, side: str, amount: float, 
                           params: Dict = None) -> Dict:
        """
        Create a market order
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order amount
            params: Additional parameters (reduce_only, position_side, etc.)
        """
        try:
            if params is None:
                params = {}
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount,
                params=params
            )
            
            logger.info(f"Market order created: {order['id']} - {side} {amount} {symbol}")
            return order
            
        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for order: {str(e)}")
            raise InsufficientFundsError(f"Not enough balance: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise ExchangeError(f"Order creation failed: {str(e)}")
    
    def close_position(self, symbol: str, position_side: str) -> Dict:
        """
        Close an open position completely
        
        Args:
            symbol: Trading pair
            position_side: 'long' or 'short'
        """
        try:
            position = self.get_position_by_symbol(symbol)
            if not position:
                logger.warning(f"No open position found for {symbol}")
                return None
            
            amount = abs(float(position['contracts']))
            side = 'sell' if position_side == 'long' else 'buy'
            
            # Close position with reduce_only flag
            order = self.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount,
                params={'reduceOnly': True}
            )
            
            logger.info(f"Position closed for {symbol}: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            raise ExchangeError(f"Position closure failed: {str(e)}")
    
    def convert_crypto(self, from_asset: str, to_asset: str, 
                      amount: float) -> Dict:
        """
        Convert one cryptocurrency to another using Convert API
        
        Args:
            from_asset: Source cryptocurrency (e.g., 'BTC')
            to_asset: Target cryptocurrency (e.g., 'USDT')
            amount: Amount to convert
        """
        try:
            # Step 1: Get quote
            quote = self.exchange.sapi_post_convert_getquote({
                'fromAsset': from_asset,
                'toAsset': to_asset,
                'fromAmount': amount,
            })
            
            quote_id = quote['quoteId']
            logger.info(f"Convert quote received: {quote_id}")
            
            # Step 2: Accept quote
            result = self.exchange.sapi_post_convert_acceptquote({
                'quoteId': quote_id,
            })
            
            logger.info(f"Conversion completed: {amount} {from_asset} -> {to_asset}")
            return result
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            # raise ExchangeError(f"Crypto conversion failed: {str(e)}")
    
    def withdraw_crypto(self, asset: str, amount: float, 
                       address: str, network: str) -> Dict:
        """
        Withdraw cryptocurrency to external address
        
        Args:
            asset: Cryptocurrency symbol (e.g., 'USDT')
            amount: Amount to withdraw
            address: External wallet address
            network: Network (e.g., 'BSC', 'ERC20', 'TRC20')
        """
        try:
            withdrawal = self.exchange.withdraw(
                code=asset,
                amount=amount,
                address=address,
                params={'network': network}
            )
            
            logger.info(f"Withdrawal initiated: {withdrawal['id']} - {amount} {asset}")
            return withdrawal
            
        except Exception as e:
            logger.error(f"Withdrawal failed: {str(e)}")
            raise ExchangeError(f"Crypto withdrawal failed: {str(e)}")
    
    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set leverage: {str(e)}")
            raise ExchangeError(f"Leverage setting failed: {str(e)}")
    
    def set_margin_mode(self, symbol: str, margin_mode: str):
        """
        Set margin mode (isolated or cross)
        
        Args:
            symbol: Trading pair
            margin_mode: 'isolated' or 'cross'
        """
        try:
            self.exchange.set_margin_mode(margin_mode, symbol)
            logger.info(f"Margin mode set to {margin_mode} for {symbol}")
        except Exception as e:
            logger.error(f"Failed to set margin mode: {str(e)}")
            raise ExchangeError(f"Margin mode setting failed: {str(e)}")


client = ExchangeClient()
print(client.exchange)