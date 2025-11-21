"""
Main application entry point for the Crypto Trading Bot
"""
import sys
import signal
import argparse
from typing import Optional

from core.exchange_client import ExchangeClient
from core.position_monitor import PositionMonitor
from core.order_executor import OrderExecutor
from core.conversion_manager import ConversionManager
from core.withdrawal_manager import WithdrawalManager
from core.state_manager import StateManager, TradingConfig, BotState
from database.db_manager import DatabaseManager
from notifications.email_notifier import EmailNotifier
from utils.logger import get_logger, setup_logger
from utils.exceptions import TradingBotError
from config.settings import (
    DEFAULT_PROFIT_THRESHOLD,
    DEFAULT_QUANTITY,
    DEFAULT_LEVERAGE,
    POSITION_MODE,
    CONVERT_TO_CRYPTO,
    WITHDRAWAL_ADDRESS
)

logger = get_logger(__name__)


class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        self.running = False
        self.db: Optional[DatabaseManager] = None
        self.exchange: Optional[ExchangeClient] = None
        self.monitor: Optional[PositionMonitor] = None
        self.executor: Optional[OrderExecutor] = None
        self.converter: Optional[ConversionManager] = None
        self.withdrawer: Optional[WithdrawalManager] = None
        self.state: Optional[StateManager] = None
        self.notifier: Optional[EmailNotifier] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize(self) -> bool:
        """Initialize all bot components"""
        try:
            logger.info("Initializing Trading Bot...")
            
            # Initialize database
            logger.info("Connecting to database...")
            self.db = DatabaseManager()
            
            # Initialize exchange client
            logger.info("Connecting to exchange...")
            self.exchange = ExchangeClient()
            
            # Initialize components
            logger.info("Initializing components...")
            self.monitor = PositionMonitor(self.exchange)
            self.executor = OrderExecutor(self.exchange)
            self.converter = ConversionManager(self.exchange)
            self.withdrawer = WithdrawalManager(self.exchange)
            self.state = StateManager(self.db)
            self.notifier = EmailNotifier(self.db)
            
            logger.info("Trading Bot initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            return False
    
    def configure(self, symbol: str, side: str, quantity: float,
                  profit_threshold: float, leverage: int = DEFAULT_LEVERAGE):
        """
        Configure trading parameters
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'long' or 'short'
            quantity: Position size
            profit_threshold: Profit target in USD
            leverage: Leverage multiplier
        """
        config = TradingConfig(
            symbol=symbol,
            side=side,
            quantity=quantity,
            leverage=leverage,
            margin_mode=POSITION_MODE,
            profit_threshold=profit_threshold
        )
        
        self.state.initialize_trading_config(config)
        logger.info(f"Bot configured: {symbol} {side} {quantity} @ {leverage}x, target: ${profit_threshold}")
    
    def start(self):
        """Start the trading bot"""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        if not self.state.trading_config:
            logger.error("Bot not configured. Call configure() first.")
            return
        
        self.running = True
        logger.info("Starting Trading Bot...")
        
        try:
            self._run_trading_cycle()
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            self.state.handle_error(str(e))
            self.notifier.send_error_alert(str(e), type(e).__name__)
    
    def _run_trading_cycle(self):
        """Execute the main trading cycle"""
        config = self.state.trading_config
        
        # Check for existing position
        existing_position = self.exchange.get_position_by_symbol(config.symbol)
        
        if existing_position and float(existing_position.get('contracts', 0)) > 0:
            logger.info(f"Found existing position for {config.symbol}")
            self.state.position_opened(existing_position)
        else:
            # Open new position if idle
            if self.state.can_open_position():
                logger.info("Opening new position...")
                self._open_position()
        
        # Start monitoring
        if self.state.is_monitoring():
            logger.info(f"Starting position monitor with target: ${config.profit_threshold}")
            self.monitor.start_monitoring(
                symbol=config.symbol,
                profit_threshold=config.profit_threshold,
                on_profit_reached=self._on_profit_reached
            )
            
            # Keep running until stopped
            while self.running and self.state.is_monitoring():
                # Check for liquidation
                if self.monitor.check_liquidation():
                    self._handle_liquidation()
                    break
                
                import time
                time.sleep(1)
    
    def _open_position(self):
        """Open a new trading position"""
        config = self.state.trading_config
        
        try:
            order = self.executor.open_position(
                symbol=config.symbol,
                side=config.side,
                quantity=config.quantity,
                leverage=config.leverage,
                margin_mode=config.margin_mode
            )
            
            # Get position details
            import time
            time.sleep(2)  # Wait for position to be registered
            
            position = self.exchange.get_position_by_symbol(config.symbol)
            if position:
                self.state.position_opened(position)
                logger.info(f"Position opened: {config.side} {config.quantity} {config.symbol}")
            
        except Exception as e:
            logger.error(f"Failed to open position: {str(e)}")
            self.state.handle_error(str(e))
            raise
    
    def _on_profit_reached(self, position: dict, profit: float):
        """Callback when profit threshold is reached"""
        logger.info(f"Profit threshold reached: ${profit:.2f}")
        
        try:
            # Step 1: Close position
            self.state.set_state(BotState.CLOSING_POSITION)
            close_order = self.executor.execute_profit_close(position, profit)
            
            if close_order:
                self.state.position_closed(close_order, profit)
                self.notifier.send_position_closed_alert(position, profit)
                
                # Step 2: Convert cryptocurrency
                self._execute_conversion(position)
                
                # Step 3: Withdraw funds
                self._execute_withdrawal()
                
                # Step 4: Auto-reset for next trade
                self.state.auto_reset()
                
                logger.info("Trade cycle completed successfully!")
                
                # Restart cycle if still running
                if self.running:
                    self._run_trading_cycle()
            
        except Exception as e:
            logger.error(f"Error in profit callback: {str(e)}")
            self.state.handle_error(str(e))
            self.notifier.send_error_alert(str(e), "ProfitCallbackError")
    
    def _execute_conversion(self, position: dict):
        """Execute cryptocurrency conversion"""
        try:
            result = self.converter.auto_convert_after_close(position)
            
            if result:
                self.state.conversion_completed(result)
                self.notifier.send_conversion_completed(result)
                logger.info("Conversion completed")
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            # Continue even if conversion fails
    
    def _execute_withdrawal(self):
        """Execute withdrawal to external wallet"""
        try:
            result = self.withdrawer.auto_withdraw_after_conversion(CONVERT_TO_CRYPTO)
            
            if result:
                self.state.withdrawal_completed(result)
                self.notifier.send_withdrawal_success(result)
                logger.info("Withdrawal completed")
            
        except Exception as e:
            logger.error(f"Withdrawal failed: {str(e)}")
            # Continue even if withdrawal fails
    
    def _handle_liquidation(self):
        """Handle account liquidation"""
        logger.critical("LIQUIDATION DETECTED!")
        
        balance = self.exchange.get_account_balance()
        current = float(balance.get('total', {}).get('USDT', 0))
        expected = self.state.trading_config.quantity * 100  # Rough estimate
        
        self.notifier.send_liquidation_alert(current, expected)
        self.state.handle_error("Account liquidation detected")
        self.stop()
    
    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping Trading Bot...")
        self.running = False
        
        if self.monitor:
            self.monitor.stop_monitoring()
        
        logger.info("Trading Bot stopped")
    
    def get_status(self) -> dict:
        """Get current bot status"""
        status = {
            'running': self.running,
            'state': self.state.get_status() if self.state else None,
        }
        
        if self.exchange and self.state and self.state.trading_config:
            pnl = self.monitor.get_current_pnl(self.state.trading_config.symbol)
            status['current_pnl'] = pnl
        
        return status
    
    def send_test_notification(self) -> bool:
        """Send a test email notification"""
        if self.notifier:
            return self.notifier.send_test_email()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Crypto Trading Bot')
    parser.add_argument('--symbol', type=str, default='BTC/USDT', help='Trading pair')
    parser.add_argument('--side', type=str, default='long', choices=['long', 'short'], help='Trade side')
    parser.add_argument('--quantity', type=float, default=DEFAULT_QUANTITY, help='Position size')
    parser.add_argument('--profit', type=float, default=DEFAULT_PROFIT_THRESHOLD, help='Profit target ($)')
    parser.add_argument('--leverage', type=int, default=DEFAULT_LEVERAGE, help='Leverage')
    parser.add_argument('--test-email', action='store_true', help='Send test email and exit')
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger()
    
    # Create bot instance
    bot = TradingBot()
    
    # Initialize
    if not bot.initialize():
        logger.error("Failed to initialize bot")
        sys.exit(1)
    
    # Test email mode
    if args.test_email:
        success = bot.send_test_notification()
        print("Test email sent!" if success else "Failed to send test email")
        sys.exit(0 if success else 1)
    
    # GUI mode
    if args.gui:
        from gui.main_window import launch_gui
        launch_gui(bot)
        sys.exit(0)
    
    # Configure bot
    bot.configure(
        symbol=args.symbol,
        side=args.side,
        quantity=args.quantity,
        profit_threshold=args.profit,
        leverage=args.leverage
    )
    
    # Start bot
    logger.info("="*50)
    logger.info("CRYPTO TRADING BOT STARTED")
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Side: {args.side.upper()}")
    logger.info(f"Quantity: {args.quantity}")
    logger.info(f"Profit Target: ${args.profit}")
    logger.info(f"Leverage: {args.leverage}x")
    logger.info("="*50)
    
    bot.start()


if __name__ == '__main__':
    main()