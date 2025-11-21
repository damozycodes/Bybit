
import os
from dotenv import load_dotenv

load_dotenv()

# Exchange Configuration
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'Bybit')
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
TESTNET = os.getenv('TESTNET', 'True').lower() == 'true'

# Trading Configuration
DEFAULT_LEVERAGE = 10
POSITION_MODE = 'isolated'  # isolated or cross
ORDER_TYPE = 'market'

# Profit Configuration
DEFAULT_PROFIT_THRESHOLD = 50  # USD
DEFAULT_QUANTITY = 0.01  # BTC or other crypto

# Conversion Configuration
CONVERT_TO_CRYPTO = 'USDT'  # Default conversion target
AUTO_CONVERT_ENABLED = True

# # Withdrawal Configuration
# AUTO_WITHDRAW_ENABLED = True
# WITHDRAWAL_ADDRESS = os.getenv('WITHDRAWAL_ADDRESS')
# WITHDRAWAL_NETWORK = 'BSC'  # BEP20, ERC20, TRC20, etc.
# MIN_WITHDRAWAL_AMOUNT = 10  # Minimum amount to trigger withdrawal

# # Notification Configuration
# EMAIL_ENABLED = True
# SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
# SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
# SMTP_USERNAME = os.getenv('SMTP_USERNAME')
# SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
# NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')

# Monitoring Configuration
MONITOR_INTERVAL = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# # Database Configuration
# DB_PATH = 'data/trading_bot.db'

# # Logging Configuration
# LOG_LEVEL = 'INFO'
# LOG_FILE = 'logs/trading_bot.log'
# MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
# BACKUP_COUNT = 5