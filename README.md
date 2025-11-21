# 🤖 Crypto Trading Bot

A fully automated cryptocurrency trading bot with position monitoring, auto-close at profit target, crypto conversion, and automatic withdrawal features.

---

## ✨ Features

### Core Trading Features
- ✅ **Position Monitoring** - Real-time monitoring of open positions
- ✅ **Auto-Close at Profit** - Automatically closes positions when profit target is reached
- ✅ **Long & Short Support** - Trade both directions
- ✅ **Isolated Margin** - Risk management with isolated margin mode
- ✅ **Configurable Leverage** - Set leverage from 1x to 125x

### Automation Features
- ✅ **Auto-Reset** - Automatically resets configuration after trade cycle
- ✅ **Crypto Conversion** - Converts profits to your preferred cryptocurrency
- ✅ **Auto-Withdrawal** - Automatically withdraws funds to external wallet
- ✅ **Fund Detection** - Waits for funds before executing automation

### Notification Features
- ✅ **Email Alerts** - Get notified on position close, withdrawals, errors
- ✅ **Liquidation Detection** - Immediate alert if account is liquidated
- ✅ **Insufficient Funds Alert** - Distinguishes between liquidation and locked funds

### User Interface
- ✅ **GUI Dashboard** - Full graphical interface with PyQt6
- ✅ **CLI Mode** - Command-line operation for servers
- ✅ **Real-time Status** - Live PnL and progress tracking
- ✅ **Activity Logs** - Detailed logging of all bot actions

---

## 📋 Requirements

- Python 3.9+
- Exchange API keys (Binance, Bybit, etc.)
- Email account for notifications (Gmail recommended)

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/crypto-trading-bot.git
cd crypto-trading-bot

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use any text editor
```

Fill in your `.env` file:
```
EXCHANGE_NAME=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
TESTNET=True

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=alerts@example.com

WITHDRAWAL_ADDRESS=0x_your_wallet_address
```

### 3. Run the Bot

```bash
# GUI Mode (recommended)
python main.py --gui

# CLI Mode with custom parameters
python main.py --symbol BTC/USDT --side long --quantity 0.01 --profit 50 --leverage 10

# Test email notifications
python main.py --test-email
```

---

## 📖 Configuration Options

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--symbol` | BTC/USDT | Trading pair |
| `--side` | long | Trade direction (long/short) |
| `--quantity` | 0.01 | Position size |
| `--profit` | 50 | Profit target in USD |
| `--leverage` | 10 | Leverage multiplier |
| `--gui` | False | Launch GUI interface |
| `--test-email` | False | Send test email and exit |

### Configuration File (config/settings.py)

```python
# Trading defaults
DEFAULT_LEVERAGE = 10
POSITION_MODE = 'isolated'
DEFAULT_PROFIT_THRESHOLD = 50
DEFAULT_QUANTITY = 0.01

# Conversion settings
CONVERT_TO_CRYPTO = 'USDT'
AUTO_CONVERT_ENABLED = True

# Withdrawal settings
AUTO_WITHDRAW_ENABLED = True
WITHDRAWAL_NETWORK = 'BSC'
MIN_WITHDRAWAL_AMOUNT = 10
```

---

## 🔄 Trading Cycle Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRADING CYCLE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CONFIGURE                                                   │
│     └─> Set symbol, side, quantity, profit target, leverage     │
│                                                                 │
│  2. OPEN POSITION                                               │
│     └─> Execute market order with isolated margin               │
│                                                                 │
│  3. MONITOR                                                     │
│     └─> Continuously check PnL against profit threshold         │
│                                                                 │
│  4. CLOSE POSITION (when profit target reached)                 │
│     └─> Execute market close order                              │
│     └─> Send email notification                                 │
│                                                                 │
│  5. CONVERT                                                     │
│     └─> Convert profits to target cryptocurrency (USDT)         │
│                                                                 │
│  6. WITHDRAW                                                    │
│     └─> Transfer funds to external wallet                       │
│     └─> Send confirmation email                                 │
│                                                                 │
│  7. AUTO-RESET                                                  │
│     └─> Reset configuration for next trade                      │
│     └─> Return to step 1                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📧 Email Notifications

The bot sends email notifications for:

| Event | Description |
|-------|-------------|
| 📈 Position Closed | When profit target is reached and position closes |
| 🔄 Conversion Complete | After cryptocurrency conversion |
| 💰 Withdrawal Success | When funds are withdrawn |
| ⚠️ Liquidation Alert | If account is liquidated |
| ⚠️ Insufficient Funds | When balance is too low |
| 🚨 Error Alert | On any critical errors |

### Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account → Security → App Passwords
   - Create a new app password for "Mail"
3. Use the app password in your `.env` file

---

## 🖥️ GUI Interface

The GUI provides:

- **Configuration Panel** - Set all trading parameters
- **Status Display** - Real-time position info and PnL
- **Progress Bar** - Visual progress toward profit target
- **Activity Log** - Live log of all bot actions
- **Control Buttons** - Start, Stop, Reset

Launch with:
```bash
python main.py --gui
```

---

## 📊 Database

The bot uses SQLite to store:

- Trade history
- Conversion records
- Withdrawal records
- Bot state (for recovery)
- Error logs
- Notification history

Database location: `data/trading_bot.db`

---

## ⚠️ Risk Warnings

1. **TESTNET FIRST** - Always test on testnet before using real funds
2. **START SMALL** - Begin with minimal amounts to verify functionality
3. **LEVERAGE RISK** - Higher leverage = higher risk of liquidation
4. **API SECURITY** - Never share API keys, use IP whitelisting
5. **NOT FINANCIAL ADVICE** - This is a tool, not investment advice

---

## 🔧 Troubleshooting

### Common Issues

**Bot not connecting to exchange:**
- Verify API keys are correct
- Check if TESTNET setting matches your keys
- Ensure API has required permissions

**Email notifications not working:**
- Verify SMTP settings
- For Gmail, use App Password (not regular password)
- Check spam folder

**Position not opening:**
- Verify sufficient balance
- Check if leverage is supported
- Ensure margin mode is correct

**Withdrawal failing:**
- Verify withdrawal address format
- Check if address is whitelisted on exchange
- Ensure minimum withdrawal amount is met

### Logs

Check logs for debugging:
```bash
# View recent logs
tail -f logs/trading_bot.log

# View trade-specific logs
tail -f logs/trades.log
```

---

## 📁 Project Structure

```
crypto-trading-bot/
├── config/
│   ├── settings.py          # Global settings
│   └── api_config.py        # Exchange API config
├── core/
│   ├── exchange_client.py   # Exchange API wrapper
│   ├── position_monitor.py  # Position monitoring
│   ├── order_executor.py    # Order execution
│   ├── conversion_manager.py # Crypto conversion
│   ├── withdrawal_manager.py # Withdrawals
│   └── state_manager.py     # Bot state & auto-reset
├── database/
│   ├── db_manager.py        # Database operations
│   ├── models.py            # Data models
│   └── schema.sql           # Database schema
├── notifications/
│   ├── email_notifier.py    # Email system
│   └── templates/           # Email templates
├── gui/
│   └── main_window.py       # GUI interface
├── utils/
│   ├── logger.py            # Logging
│   ├── validators.py        # Input validation
│   ├── helpers.py           # Utility functions
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Unit tests
├── logs/                    # Log files
├── data/                    # Database
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
└── README.md               # This file
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_exchange_client.py

# Run with coverage
pytest --cov=core tests/
```

---

## 📜 License

MIT License - Feel free to use and modify.

---

## 🤝 Support

For issues or feature requests, please open a GitHub issue.

---

## 📈 Roadmap

- [ ] Multi-position support
- [ ] Trailing stop-loss
- [ ] DCA (Dollar Cost Averaging) mode
- [ ] Telegram notifications
- [ ] Web dashboard
- [ ] More exchange support (Bybit, OKX, etc.)