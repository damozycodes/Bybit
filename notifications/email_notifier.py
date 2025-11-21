import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.logger import get_logger
from config.settings import (
    EMAIL_ENABLED,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    NOTIFICATION_EMAIL
)

logger = get_logger(__name__)


class EmailNotifier:
    """Handle email notifications"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.enabled = EMAIL_ENABLED
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.username = SMTP_USERNAME
        self.password = SMTP_PASSWORD
        self.recipient = NOTIFICATION_EMAIL
        
        if not self._validate_config():
            logger.warning("Email configuration incomplete - notifications disabled")
            self.enabled = False
    
    def _validate_config(self) -> bool:
        """Validate email configuration"""
        return all([
            self.smtp_server,
            self.smtp_port,
            self.username,
            self.password,
            self.recipient
        ])
    
    def _send_email(self, subject: str, body_html: str, body_text: str) -> bool:
        """
        Send an email
        
        Args:
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.warning("Email notifications disabled")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.username
            message['To'] = self.recipient
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            message.attach(part1)
            message.attach(part2)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _load_template(self, template_name: str, **kwargs) -> str:
        """Load and render email template"""
        try:
            template_path = f"notifications/templates/{template_name}"
            
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Simple template variable replacement
            for key, value in kwargs.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {str(e)}")
            return ""
    
    def send_liquidation_alert(self, balance: float, expected_balance: float) -> bool:
        """
        Send liquidation alert email
        
        Args:
            balance: Current balance
            expected_balance: Expected balance
        
        Returns:
            True if sent successfully
        """
        subject = "⚠️ URGENT: Account Liquidation Detected"
        
        body_html = self._load_template(
            'liquidation.html',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            current_balance=f"${balance:.2f}",
            expected_balance=f"${expected_balance:.2f}",
            loss=f"${expected_balance - balance:.2f}"
        )
        
        body_text = f"""
URGENT: Account Liquidation Detected

Your trading account has been liquidated!

Details:
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Current Balance: ${balance:.2f}
- Expected Balance: ${expected_balance:.2f}
- Estimated Loss: ${expected_balance - balance:.2f}

This alert indicates that your positions were forcefully closed due to insufficient margin.

Please review your account immediately and adjust your risk management strategy.

Bot Status: PAUSED - Awaiting manual intervention
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'liquidation',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        else:
            self.db.update_notification_status(
                notification_id,
                'failed',
                datetime.now().isoformat()
            )
        
        return success
    
    def send_position_closed_alert(self, position: Dict, profit: float) -> bool:
        """
        Send position closed notification
        
        Args:
            position: Position details
            profit: Realized profit
        
        Returns:
            True if sent successfully
        """
        profit_emoji = "📈" if profit > 0 else "📉"
        subject = f"{profit_emoji} Position Closed - {'Profit' if profit > 0 else 'Loss'}: ${abs(profit):.2f}"
        
        body_html = self._load_template(
            'position_closed.html',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol=position.get('symbol', 'N/A'),
            side=position.get('side', 'N/A').upper(),
            entry_price=f"${position.get('entryPrice', 0):.2f}",
            exit_price=f"${position.get('price', 0):.2f}",
            quantity=position.get('contracts', 0),
            profit=f"${profit:.2f}",
            profit_color="green" if profit > 0 else "red"
        )
        
        body_text = f"""
Position Closed Successfully

A trading position has been automatically closed by the bot.

Position Details:
- Symbol: {position.get('symbol', 'N/A')}
- Side: {position.get('side', 'N/A').upper()}
- Entry Price: ${position.get('entryPrice', 0):.2f}
- Exit Price: ${position.get('price', 0):.2f}
- Quantity: {position.get('contracts', 0)}
- Realized Profit/Loss: ${profit:.2f}

Closed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Next Actions:
- Conversion to {self._get_target_crypto()} in progress...
- Withdrawal will follow automatically
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'position_closed',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        else:
            self.db.update_notification_status(
                notification_id,
                'failed',
                datetime.now().isoformat()
            )
        
        return success
    
    def send_conversion_completed(self, conversion: Dict) -> bool:
        """
        Send conversion completed notification
        
        Args:
            conversion: Conversion details
        
        Returns:
            True if sent successfully
        """
        subject = f"✅ Conversion Completed: {conversion.get('from_asset')} → {conversion.get('to_asset')}"
        
        body_html = self._load_template(
            'conversion_completed.html',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            from_asset=conversion.get('from_asset', 'N/A'),
            to_asset=conversion.get('to_asset', 'N/A'),
            from_amount=conversion.get('from_amount', 0),
            to_amount=conversion.get('to_amount', 0),
            exchange_rate=conversion.get('exchange_rate', 0)
        )
        
        body_text = f"""
Cryptocurrency Conversion Completed

The bot has successfully converted your cryptocurrency.

Conversion Details:
- From: {conversion.get('from_amount', 0)} {conversion.get('from_asset', 'N/A')}
- To: {conversion.get('to_amount', 0)} {conversion.get('to_asset', 'N/A')}
- Exchange Rate: {conversion.get('exchange_rate', 0)}
- Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Next Action:
- Automatic withdrawal to external wallet in progress...
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'conversion_completed',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        
        return success
    
    def send_withdrawal_success(self, withdrawal: Dict) -> bool:
        """
        Send withdrawal success notification
        
        Args:
            withdrawal: Withdrawal details
        
        Returns:
            True if sent successfully
        """
        subject = f"💰 Withdrawal Successful: {withdrawal.get('amount')} {withdrawal.get('asset')}"
        
        body_html = self._load_template(
            'withdrawal_success.html',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            asset=withdrawal.get('asset', 'N/A'),
            amount=withdrawal.get('amount', 0),
            address=withdrawal.get('address', 'N/A'),
            network=withdrawal.get('network', 'N/A'),
            tx_id=withdrawal.get('tx_id', 'Pending'),
            fee=withdrawal.get('fee', 0)
        )
        
        body_text = f"""
Cryptocurrency Withdrawal Successful

The bot has successfully initiated a withdrawal to your external wallet.

Withdrawal Details:
- Asset: {withdrawal.get('asset', 'N/A')}
- Amount: {withdrawal.get('amount', 0)}
- Network: {withdrawal.get('network', 'N/A')}
- Destination Address: {withdrawal.get('address', 'N/A')}
- Transaction ID: {withdrawal.get('tx_id', 'Pending')}
- Network Fee: {withdrawal.get('fee', 0)}
- Initiated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Trade Cycle Complete:
The bot has completed a full trade cycle and has been reset for the next trade.

Bot Status: READY - Monitoring for next opportunity
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'withdrawal_success',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        
        return success
    
    def send_insufficient_funds_alert(self, required: float, available: float, 
                                     reason: str = "trading") -> bool:
        """
        Send insufficient funds alert
        
        Args:
            required: Required amount
            available: Available amount
            reason: Reason for the alert
        
        Returns:
            True if sent successfully
        """
        subject = f"⚠️ Insufficient Funds Alert - {reason.title()}"
        
        body_text = f"""
Insufficient Funds Detected

The bot detected insufficient funds for {reason}.

Details:
- Required Amount: ${required:.2f}
- Available Amount: ${available:.2f}
- Shortage: ${required - available:.2f}
- Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: This is NOT due to liquidation. The funds may be locked in an open position.

Action Required:
- Check your open positions
- Ensure sufficient balance for trading
- Review bot configuration

Bot Status: PAUSED - Awaiting sufficient funds
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #ff9800;">⚠️ Insufficient Funds Alert</h2>
    <p>The bot detected insufficient funds for {reason}.</p>
    
    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ff9800;">
        <h3>Details:</h3>
        <ul>
            <li><strong>Required Amount:</strong> ${required:.2f}</li>
            <li><strong>Available Amount:</strong> ${available:.2f}</li>
            <li><strong>Shortage:</strong> <span style="color: #d32f2f;">${required - available:.2f}</span></li>
            <li><strong>Detected at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
    </div>
    
    <p><strong>Note:</strong> This is NOT due to liquidation. The funds may be locked in an open position.</p>
    
    <h3>Action Required:</h3>
    <ul>
        <li>Check your open positions</li>
        <li>Ensure sufficient balance for trading</li>
        <li>Review bot configuration</li>
    </ul>
    
    <p style="color: #666; margin-top: 20px;">
        Bot Status: <strong>PAUSED</strong> - Awaiting sufficient funds
    </p>
</body>
</html>
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'insufficient_funds',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        
        return success
    
    def send_error_alert(self, error_message: str, error_type: str = "Unknown") -> bool:
        """
        Send error alert email
        
        Args:
            error_message: Error message
            error_type: Type of error
        
        Returns:
            True if sent successfully
        """
        subject = f"🚨 Bot Error Alert: {error_type}"
        
        body_text = f"""
Bot Error Detected

An error has occurred in the trading bot.

Error Details:
- Type: {error_type}
- Message: {error_message}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The bot has been paused to prevent further issues.

Action Required:
- Review the error details
- Check bot logs for more information
- Restart the bot if necessary

Bot Status: ERROR - Manual intervention required
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #d32f2f;">🚨 Bot Error Alert</h2>
    <p>An error has occurred in the trading bot.</p>
    
    <div style="background-color: #ffebee; padding: 15px; border-left: 4px solid #d32f2f;">
        <h3>Error Details:</h3>
        <ul>
            <li><strong>Type:</strong> {error_type}</li>
            <li><strong>Message:</strong> {error_message}</li>
            <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
    </div>
    
    <p>The bot has been paused to prevent further issues.</p>
    
    <h3>Action Required:</h3>
    <ul>
        <li>Review the error details</li>
        <li>Check bot logs for more information</li>
        <li>Restart the bot if necessary</li>
    </ul>
    
    <p style="color: #d32f2f; margin-top: 20px;">
        Bot Status: <strong>ERROR</strong> - Manual intervention required
    </p>
</body>
</html>
        """
        
        # Save to database
        notification_id = self.db.save_notification({
            'notification_type': 'error',
            'recipient': self.recipient,
            'subject': subject,
            'message': body_text,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })
        
        # Send email
        success = self._send_email(subject, body_html, body_text)
        
        # Update notification status
        if success:
            self.db.update_notification_status(
                notification_id,
                'sent',
                datetime.now().isoformat()
            )
        
        return success
    
    def _get_target_crypto(self) -> str:
        """Get target crypto from config"""
        from config.settings import CONVERT_TO_CRYPTO
        return CONVERT_TO_CRYPTO
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        subject = "✅ Trading Bot - Test Email"
        
        body_text = f"""
Test Email from Trading Bot

This is a test email to verify your notification settings.

If you received this email, your email notifications are configured correctly.

Configuration Details:
- SMTP Server: {self.smtp_server}
- Port: {self.smtp_port}
- From: {self.username}
- To: {self.recipient}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your trading bot is ready to send notifications!
        """
        
        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4caf50;"> Trading Bot - Test Email</h2>
    <p>This is a test email to verify your notification settings.</p>
    
    <div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50;">
        <p>If you received this email, your email notifications are configured correctly.</p>
    </div>
    
    <h3>Configuration Details:</h3>
    <ul>
        <li><strong>SMTP Server:</strong> {self.smtp_server}</li>
        <li><strong>Port:</strong> {self.smtp_port}</li>
        <li><strong>From:</strong> {self.username}</li>
        <li><strong>To:</strong> {self.recipient}</li>
        <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
    </ul>
    
    <p style="color: #4caf50; margin-top: 20px;">
        <strong>Your trading bot is ready to send notifications!</strong>
    </p>
</body>
</html>
        """
        
        return self._send_email(subject, body_html, body_text)