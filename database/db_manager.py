"""
Database manager for handling all database operations
"""
import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager
from database.models import Trade, Conversion, Withdrawal, BotState, ErrorLog, Notification
from utils.logger import get_logger
from config.settings import DB_PATH

logger = get_logger(__name__)


class DatabaseManager:
    """Handle all database operations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database with schema"""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    # ============ TRADE OPERATIONS ============
    
    def save_trade(self, trade_data: Dict) -> int:
        """Save a new trade record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO trades (
                        symbol, side, entry_price, quantity, leverage,
                        status, opened_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_data.get('symbol'),
                    trade_data.get('side'),
                    trade_data.get('entry_price'),
                    trade_data.get('quantity'),
                    trade_data.get('leverage', 10),
                    trade_data.get('status', 'open'),
                    trade_data.get('opened_at'),
                    trade_data.get('notes'),
                ))
                
                trade_id = cursor.lastrowid
                logger.info(f"Trade saved with ID: {trade_id}")
                return trade_id
                
        except Exception as e:
            logger.error(f"Failed to save trade: {str(e)}")
            raise
    
    def update_trade_status(self, symbol: str, status: str, 
                           exit_price: Optional[float] = None,
                           profit: Optional[float] = None,
                           closed_at: Optional[str] = None):
        """Update trade status and exit details"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE trades
                    SET status = ?, exit_price = ?, profit = ?, closed_at = ?
                    WHERE symbol = ? AND status = 'open'
                    ORDER BY opened_at DESC
                    LIMIT 1
                """, (status, exit_price, profit, closed_at, symbol))
                
                logger.info(f"Trade status updated for {symbol}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update trade status: {str(e)}")
            raise
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM trades
                    WHERE status = 'open'
                    ORDER BY opened_at DESC
                """)
                
                trades = [dict(row) for row in cursor.fetchall()]
                return trades
                
        except Exception as e:
            logger.error(f"Failed to get open trades: {str(e)}")
            return []
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get trade history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM trades
                    ORDER BY opened_at DESC
                    LIMIT ?
                """, (limit,))
                
                trades = [dict(row) for row in cursor.fetchall()]
                return trades
                
        except Exception as e:
            logger.error(f"Failed to get trade history: {str(e)}")
            return []
    
    def get_trade_statistics(self) -> Dict:
        """Get trading statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(profit) as total_profit,
                        AVG(profit) as avg_profit,
                        MAX(profit) as max_profit,
                        MIN(profit) as min_profit
                    FROM trades
                    WHERE status = 'closed'
                """)
                
                row = cursor.fetchone()
                stats = dict(row) if row else {}
                
                # Calculate win rate
                if stats.get('total_trades', 0) > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                else:
                    stats['win_rate'] = 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get trade statistics: {str(e)}")
            return {}
    
    # ============ CONVERSION OPERATIONS ============
    
    def save_conversion(self, conversion_data: Dict) -> int:
        """Save a conversion record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO conversions (
                        trade_id, from_asset, to_asset, from_amount, to_amount,
                        exchange_rate, quote_id, status, executed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversion_data.get('trade_id'),
                    conversion_data.get('from_asset'),
                    conversion_data.get('to_asset'),
                    conversion_data.get('from_amount'),
                    conversion_data.get('to_amount'),
                    conversion_data.get('exchange_rate'),
                    conversion_data.get('quote_id'),
                    conversion_data.get('status', 'pending'),
                    conversion_data.get('executed_at'),
                ))
                
                conversion_id = cursor.lastrowid
                logger.info(f"Conversion saved with ID: {conversion_id}")
                return conversion_id
                
        except Exception as e:
            logger.error(f"Failed to save conversion: {str(e)}")
            raise
    
    def get_conversions_by_trade(self, trade_id: int) -> List[Dict]:
        """Get conversions for a specific trade"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM conversions
                    WHERE trade_id = ?
                    ORDER BY executed_at DESC
                """, (trade_id,))
                
                conversions = [dict(row) for row in cursor.fetchall()]
                return conversions
                
        except Exception as e:
            logger.error(f"Failed to get conversions: {str(e)}")
            return []
    
    # ============ WITHDRAWAL OPERATIONS ============
    
    def save_withdrawal(self, withdrawal_data: Dict) -> int:
        """Save a withdrawal record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO withdrawals (
                        trade_id, conversion_id, asset, amount, address,
                        network, tx_id, status, fee, executed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    withdrawal_data.get('trade_id'),
                    withdrawal_data.get('conversion_id'),
                    withdrawal_data.get('asset'),
                    withdrawal_data.get('amount'),
                    withdrawal_data.get('address'),
                    withdrawal_data.get('network'),
                    withdrawal_data.get('tx_id'),
                    withdrawal_data.get('status', 'pending'),
                    withdrawal_data.get('fee'),
                    withdrawal_data.get('executed_at'),
                ))
                
                withdrawal_id = cursor.lastrowid
                logger.info(f"Withdrawal saved with ID: {withdrawal_id}")
                return withdrawal_id
                
        except Exception as e:
            logger.error(f"Failed to save withdrawal: {str(e)}")
            raise
    
    def get_withdrawals_by_trade(self, trade_id: int) -> List[Dict]:
        """Get withdrawals for a specific trade"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM withdrawals
                    WHERE trade_id = ?
                    ORDER BY executed_at DESC
                """, (trade_id,))
                
                withdrawals = [dict(row) for row in cursor.fetchall()]
                return withdrawals
                
        except Exception as e:
            logger.error(f"Failed to get withdrawals: {str(e)}")
            return []
    def save_bot_state(self, state_data: Dict):
        """Save or update bot state"""
        try:
            with self.get_connection() as conn:
                # Check if state exists
                cursor = conn.execute("SELECT id FROM bot_state ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    # Update existing state
                    conn.execute("""
                        UPDATE bot_state
                        SET current_state = ?, trading_config = ?, 
                            active_position = ?, last_updated = ?
                        WHERE id = ?
                    """, (
                        state_data.get('current_state'),
                        state_data.get('trading_config'),
                        state_data.get('active_position'),
                        state_data.get('last_updated'),
                        row['id']
                    ))
                else:
                    # Insert new state
                    conn.execute("""
                        INSERT INTO bot_state (
                            current_state, trading_config, active_position, last_updated
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        state_data.get('current_state'),
                        state_data.get('trading_config'),
                        state_data.get('active_position'),
                        state_data.get('last_updated'),
                    ))
                
                logger.debug("Bot state saved")
                
        except Exception as e:
            logger.error(f"Failed to save bot state: {str(e)}")
            raise
    
    def get_bot_state(self) -> Optional[Dict]:
        """Get current bot state"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM bot_state
                    ORDER BY id DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get bot state: {str(e)}")
            return None
    
    # ============ ERROR LOG OPERATIONS ============
    
    def save_error_log(self, error_data: Dict) -> int:
        """Save an error log"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO error_logs (
                        timestamp, error_type, error_message, state, 
                        active_position, stack_trace
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    error_data.get('timestamp'),
                    error_data.get('error_type', 'Unknown'),
                    error_data.get('error_message'),
                    error_data.get('state'),
                    error_data.get('active_position'),
                    error_data.get('stack_trace'),
                ))
                
                error_id = cursor.lastrowid
                logger.info(f"Error log saved with ID: {error_id}")
                return error_id
                
        except Exception as e:
            logger.error(f"Failed to save error log: {str(e)}")
            raise
    
    def get_error_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent error logs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM error_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                errors = [dict(row) for row in cursor.fetchall()]
                return errors
                
        except Exception as e:
            logger.error(f"Failed to get error logs: {str(e)}")
            return []
    
    # ============ NOTIFICATION OPERATIONS ============
    
    def save_notification(self, notification_data: Dict) -> int:
        """Save a notification record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO notifications (
                        notification_type, recipient, subject, message,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    notification_data.get('notification_type'),
                    notification_data.get('recipient'),
                    notification_data.get('subject'),
                    notification_data.get('message'),
                    notification_data.get('status', 'pending'),
                    notification_data.get('created_at', datetime.now().isoformat()),
                ))
                
                notification_id = cursor.lastrowid
                logger.info(f"Notification saved with ID: {notification_id}")
                return notification_id
                
        except Exception as e:
            logger.error(f"Failed to save notification: {str(e)}")
            raise
    
    def update_notification_status(self, notification_id: int, status: str, sent_at: str):
        """Update notification status"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE notifications
                    SET status = ?, sent_at = ?
                    WHERE id = ?
                """, (status, sent_at, notification_id))
                
                logger.debug(f"Notification {notification_id} status updated to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update notification status: {str(e)}")
            raise
    
    def get_pending_notifications(self) -> List[Dict]:
        """Get pending notifications"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM notifications
                    WHERE status = 'pending'
                    ORDER BY created_at ASC
                """)
                
                notifications = [dict(row) for row in cursor.fetchall()]
                return notifications
                
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {str(e)}")
            return []
    
    # ============ UTILITY OPERATIONS ============
    
    def clear_all_data(self):
        """Clear all data from database (for testing/reset)"""
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM trades")
                conn.execute("DELETE FROM conversions")
                conn.execute("DELETE FROM withdrawals")
                conn.execute("DELETE FROM bot_state")
                conn.execute("DELETE FROM error_logs")
                conn.execute("DELETE FROM notifications")
                
                logger.warning("All database data cleared")
                
        except Exception as e:
            logger.error(f"Failed to clear database: {str(e)}")
            raise
    
    def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            raise
    
    def vacuum_database(self):
        """Optimize database (reclaim space)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database optimized")
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {str(e)}")
            raise