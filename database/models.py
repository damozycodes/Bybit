"""
Database models and schemas
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    """Trade record model"""
    id: Optional[int] = None
    symbol: str = ''
    side: str = ''  # 'long' or 'short'
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    quantity: float = 0.0
    leverage: int = 10
    profit: Optional[float] = None
    status: str = 'open'  # 'open', 'closed', 'liquidated'
    opened_at: str = ''
    closed_at: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'profit': self.profit,
            'status': self.status,
            'opened_at': self.opened_at,
            'closed_at': self.closed_at,
            'notes': self.notes,
        }


@dataclass
class Conversion:
    """Conversion record model"""
    id: Optional[int] = None
    trade_id: Optional[int] = None
    from_asset: str = ''
    to_asset: str = ''
    from_amount: float = 0.0
    to_amount: float = 0.0
    exchange_rate: float = 0.0
    quote_id: Optional[str] = None
    status: str = 'pending'  # 'pending', 'completed', 'failed'
    executed_at: str = ''
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'from_asset': self.from_asset,
            'to_asset': self.to_asset,
            'from_amount': self.from_amount,
            'to_amount': self.to_amount,
            'exchange_rate': self.exchange_rate,
            'quote_id': self.quote_id,
            'status': self.status,
            'executed_at': self.executed_at,
        }


@dataclass
class Withdrawal:
    """Withdrawal record model"""
    id: Optional[int] = None
    trade_id: Optional[int] = None
    conversion_id: Optional[int] = None
    asset: str = ''
    amount: float = 0.0
    address: str = ''
    network: str = ''
    tx_id: Optional[str] = None
    status: str = 'pending'  # 'pending', 'completed', 'failed'
    fee: Optional[float] = None
    executed_at: str = ''
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'conversion_id': self.conversion_id,
            'asset': self.asset,
            'amount': self.amount,
            'address': self.address,
            'network': self.network,
            'tx_id': self.tx_id,
            'status': self.status,
            'fee': self.fee,
            'executed_at': self.executed_at,
        }


@dataclass
class BotState:
    """Bot state record model"""
    id: Optional[int] = None
    current_state: str = 'idle'
    trading_config: Optional[str] = None  # JSON
    active_position: Optional[str] = None  # JSON
    last_updated: str = ''
    
    def to_dict(self):
        return {
            'id': self.id,
            'current_state': self.current_state,
            'trading_config': self.trading_config,
            'active_position': self.active_position,
            'last_updated': self.last_updated,
        }


@dataclass
class ErrorLog:
    """Error log record model"""
    id: Optional[int] = None
    timestamp: str = ''
    error_type: str = ''
    error_message: str = ''
    state: Optional[str] = None
    active_position: Optional[str] = None  # JSON
    stack_trace: Optional[str] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'state': self.state,
            'active_position': self.active_position,
            'stack_trace': self.stack_trace,
        }


@dataclass
class Notification:
    """Notification record model"""
    id: Optional[int] = None
    notification_type: str = ''  # 'liquidation', 'position_closed', 'withdrawal', etc.
    recipient: str = ''
    subject: str = ''
    message: str = ''
    status: str = 'pending'  # 'pending', 'sent', 'failed'
    sent_at: Optional[str] = None
    created_at: str = ''
    
    def to_dict(self):
        return {
            'id': self.id,
            'notification_type': self.notification_type,
            'recipient': self.recipient,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'sent_at': self.sent_at,
            'created_at': self.created_at,
        }