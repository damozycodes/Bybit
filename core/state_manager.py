"""
Bot state management and auto-reset functionality
"""
import json
import time
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class BotState(Enum):
    """Bot operational states"""
    IDLE = "idle"
    MONITORING = "monitoring"
    CLOSING_POSITION = "closing_position"
    CONVERTING = "converting"
    WITHDRAWING = "withdrawing"
    RESETTING = "resetting"
    ERROR = "error"


class TradingConfig:
    """Trading configuration data structure"""
    
    def __init__(self, **kwargs):
        self.symbol: str = kwargs.get('symbol', 'BTC/USDT')
        self.side: str = kwargs.get('side', 'long')  # 'long' or 'short'
        self.quantity: float = kwargs.get('quantity', 0.01)
        self.leverage: int = kwargs.get('leverage', 10)
        self.margin_mode: str = kwargs.get('margin_mode', 'isolated')
        self.profit_threshold: float = kwargs.get('profit_threshold', 50.0)
        self.entry_price: Optional[float] = kwargs.get('entry_price', None)
        self.position_opened_at: Optional[datetime] = kwargs.get('position_opened_at', None)
        
    def to_dict(self) -> Dict:
        """Convert config to dictionary"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'margin_mode': self.margin_mode,
            'profit_threshold': self.profit_threshold,
            'entry_price': self.entry_price,
            'position_opened_at': self.position_opened_at.isoformat() if self.position_opened_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradingConfig':
        """Create config from dictionary"""
        if data.get('position_opened_at'):
            data['position_opened_at'] = datetime.fromisoformat(data['position_opened_at'])
        return cls(**data)
    
    def reset(self):
        """Reset dynamic fields after position close"""
        self.entry_price = None
        self.position_opened_at = None
        logger.info("Trading config reset - ready for new position")


class StateManager:
    """Manage bot state and handle auto-reset logic"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.current_state: BotState = BotState.IDLE
        self.trading_config: Optional[TradingConfig] = None
        self.active_position: Optional[Dict] = None
        self.last_closed_position: Optional[Dict] = None
        self.trade_history: list = []
        
        # Load saved state if exists
        self._load_state()
    
    def initialize_trading_config(self, config: TradingConfig):
        """Initialize trading configuration"""
        self.trading_config = config
        self._save_state()
        logger.info(f"Trading config initialized: {config.to_dict()}")
    
    def update_trading_config(self, **updates):
        """Update trading configuration parameters"""
        if not self.trading_config:
            logger.error("No trading config to update")
            return
        
        for key, value in updates.items():
            if hasattr(self.trading_config, key):
                setattr(self.trading_config, key, value)
                logger.info(f"Updated {key} to {value}")
        
        self._save_state()
    
    def set_state(self, new_state: BotState):
        """Change bot state"""
        old_state = self.current_state
        self.current_state = new_state
        logger.info(f"State changed: {old_state.value} -> {new_state.value}")
        self._save_state()
    
    def is_idle(self) -> bool:
        """Check if bot is idle"""
        return self.current_state == BotState.IDLE
    
    def is_monitoring(self) -> bool:
        """Check if bot is monitoring"""
        return self.current_state == BotState.MONITORING
    
    def can_open_position(self) -> bool:
        """Check if bot can open a new position"""
        return self.current_state in [BotState.IDLE, BotState.RESETTING]
    
    def position_opened(self, position_data: Dict):
        """Record that a position was opened"""
        self.active_position = position_data
        
        if self.trading_config:
            self.trading_config.entry_price = float(position_data.get('entryPrice', 0))
            self.trading_config.position_opened_at = datetime.now()
        
        self.set_state(BotState.MONITORING)
        
        # Save to database
        self.db.save_trade({
            'symbol': position_data.get('symbol'),
            'side': position_data.get('side'),
            'entry_price': position_data.get('entryPrice'),
            'quantity': position_data.get('contracts'),
            'leverage': self.trading_config.leverage if self.trading_config else 10,
            'opened_at': datetime.now().isoformat(),
            'status': 'open'
        })
        
        logger.info(f"Position recorded: {position_data.get('symbol')}")
    
    def position_closed(self, close_data: Dict, profit: float):
        """Record that a position was closed"""
        self.last_closed_position = {
            **self.active_position,
            **close_data,
            'profit': profit,
            'closed_at': datetime.now()
        }
        
        # Update trade in database
        self.db.update_trade_status(
            symbol=close_data.get('symbol'),
            status='closed',
            exit_price=close_data.get('price'),
            profit=profit,
            closed_at=datetime.now().isoformat()
        )
        
        self.active_position = None
        self.set_state(BotState.CONVERTING)
        
        logger.info(f"Position closed with profit: ${profit:.2f}")
    
    def conversion_completed(self, conversion_data: Dict):
        """Record that conversion was completed"""
        if self.last_closed_position:
            self.last_closed_position['conversion'] = conversion_data
        
        self.set_state(BotState.WITHDRAWING)
        logger.info("Conversion completed")
    
    def withdrawal_completed(self, withdrawal_data: Dict):
        """Record that withdrawal was completed"""
        if self.last_closed_position:
            self.last_closed_position['withdrawal'] = withdrawal_data
        
        # Save complete trade cycle to history
        self.trade_history.append(self.last_closed_position)
        
        # Trigger auto-reset
        self.auto_reset()
    
    def auto_reset(self):
        """Automatically reset configuration for next trade"""
        logger.info("Starting auto-reset process...")
        
        self.set_state(BotState.RESETTING)
        
        # Reset trading config
        if self.trading_config:
            self.trading_config.reset()
        
        # Clear last closed position
        self.last_closed_position = None
        
        # Return to idle state
        self.set_state(BotState.IDLE)
        
        logger.info("Auto-reset completed - Bot ready for new trade")
    
    def handle_error(self, error_message: str):
        """Handle error state"""
        self.set_state(BotState.ERROR)
        logger.error(f"Bot entered error state: {error_message}")
        
        # Save error to database
        self.db.save_error_log({
            'timestamp': datetime.now().isoformat(),
            'error_message': error_message,
            'state': self.current_state.value,
            'active_position': json.dumps(self.active_position) if self.active_position else None
        })
    
    def recover_from_error(self):
        """Attempt to recover from error state"""
        logger.info("Attempting to recover from error state...")
        
        # If we have an active position, go back to monitoring
        if self.active_position:
            self.set_state(BotState.MONITORING)
        else:
            self.set_state(BotState.IDLE)
        
        logger.info(f"Recovered to state: {self.current_state.value}")
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        status = {
            'state': self.current_state.value,
            'has_active_position': self.active_position is not None,
            'trading_config': self.trading_config.to_dict() if self.trading_config else None,
            'total_trades': len(self.trade_history),
            'last_trade_profit': self.trade_history[-1].get('profit', 0) if self.trade_history else 0,
        }
        
        if self.active_position:
            status['active_position'] = {
                'symbol': self.active_position.get('symbol'),
                'side': self.active_position.get('side'),
                'entry_price': self.active_position.get('entryPrice'),
                'contracts': self.active_position.get('contracts'),
            }
        
        return status
    
    def _save_state(self):
        """Save current state to database"""
        try:
            state_data = {
                'current_state': self.current_state.value,
                'trading_config': json.dumps(self.trading_config.to_dict()) if self.trading_config else None,
                'active_position': json.dumps(self.active_position) if self.active_position else None,
                'last_updated': datetime.now().isoformat()
            }
            
            self.db.save_bot_state(state_data)
            
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
    
    def _load_state(self):
        """Load saved state from database"""
        try:
            state_data = self.db.get_bot_state()
            
            if state_data:
                self.current_state = BotState(state_data.get('current_state', 'idle'))
                
                if state_data.get('trading_config'):
                    config_dict = json.loads(state_data['trading_config'])
                    self.trading_config = TradingConfig.from_dict(config_dict)
                
                if state_data.get('active_position'):
                    self.active_position = json.loads(state_data['active_position'])
                
                logger.info(f"State loaded: {self.current_state.value}")
            else:
                logger.info("No saved state found, starting fresh")
                
        except Exception as e:
            logger.error(f"Failed to load state: {str(e)}")
    
    def force_reset(self):
        """Force complete reset of bot state"""
        logger.warning("Forcing complete state reset")
        
        self.current_state = BotState.IDLE
        self.active_position = None
        self.last_closed_position = None
        
        if self.trading_config:
            self.trading_config.reset()
        
        self._save_state()
        logger.info("Force reset completed")
    
    def get_trade_statistics(self) -> Dict:
        """Get trading statistics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'total_profit': 0.0,
                'win_rate': 0.0,
                'average_profit': 0.0,
            }
        
        total_trades = len(self.trade_history)
        profits = [trade.get('profit', 0) for trade in self.trade_history]
        total_profit = sum(profits)
        winning_trades = sum(1 for p in profits if p > 0)
        
        return {
            'total_trades': total_trades,
            'total_profit': total_profit,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'average_profit': total_profit / total_trades if total_trades > 0 else 0,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
        }