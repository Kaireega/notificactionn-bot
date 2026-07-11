# 🤖 Forex Trading Bot - Market Adaptive System

A comprehensive, AI-powered forex trading bot with multi-timeframe analysis, risk management, and real-time notifications.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Components](#components)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)

## 🎯 Overview

This forex trading bot combines traditional technical analysis with AI-powered decision making to identify profitable trading opportunities across multiple timeframes. It features comprehensive risk management, real-time notifications, and detailed trade recording.

## ✨ Features

### 🤖 **AI-Powered Analysis**
- Multi-timeframe analysis (M1, M5, M15, H1)
- AI-driven market condition detection
- Consensus-based trade recommendations
- Confidence scoring for all signals

### 📊 **Technical Analysis**
- RSI, MACD, Bollinger Bands, ATR, Keltner Channels
- Candlestick pattern recognition
- Support/Resistance level detection
- Volatility and momentum analysis

### 🛡️ **Risk Management**
- Position sizing based on account balance
- Daily loss limits and correlation checks
- Dynamic stop-loss and take-profit calculation
- Market hours and volatility filters

### 📱 **Real-Time Notifications**
- Telegram notifications for trade alerts
- Email notifications for important events
- Startup summaries with performance metrics
- Error alerts and system status updates

### 📈 **Comprehensive Recording**
- Excel-based trade recording with 7 detailed sheets
- Complete AI outputs and decision data
- Technical indicators for each timeframe
- Risk assessment and market context

## 🏗️ Architecture

```
📁 Project Structure
├── 🤖 trading_bot/          # Main trading bot
│   ├── 📊 src/                      # Source code
│   │   ├── 🧠 ai/                   # AI analysis layer
│   │   ├── 📈 data/                 # Data collection
│   │   ├── 🎯 decision/             # Decision making
│   │   ├── 📱 notifications/        # Notifications
│   │   └── 🔧 utils/                # Utilities
│   ├── 📋 config/                   # Configuration
│   ├── 📊 logs/                     # Logs and trade records
│   └── 🧪 tests/                    # Test files
├── 📊 technicals/                   # Technical indicators
├── 🔌 api/                          # API integrations
├── 📊 data/                         # Historical data
├── 🧪 tests/                        # Test suites
└── 📚 docs/                         # Documentation
```

## 🚀 Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd forex-trading-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configuration**

```bash
# Copy environment template
cp trading_bot/env_example.txt config.env

# Edit configuration
nano config.env
```

Required configuration:
```env
# OANDA API Configuration
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here
OANDA_URL=https://api-fxpractice.oanda.com/v3

# OpenAI API (for AI analysis)
OPENAI_API_KEY=your_openai_api_key_here

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Email (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 3. **Run the Bot**

```bash
# Start the trading bot (from project root)
python start_bot.py

# Or directly from the trading_bot directory
cd trading_bot
python main.py
```

## ⚙️ Configuration

### **Trading Pairs**
Configure in `trading_bot/src/utils/config.py`:
```python
trading_pairs = ["EUR_USD", "USD_JPY", "GBP_JPY"]
```

### **Risk Management**
```python
risk_percentage = 1.0  # 1% risk per trade
max_daily_loss = 5.0   # 5% daily loss limit
max_trades_per_day = 10
```

### **AI Analysis**
```python
ai_confidence_threshold = 0.6  # Minimum confidence for trades
timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
```

## 🔧 Components

### **1. Data Layer** (`src/data/`)
- Real-time price data collection
- Historical data management
- Market context analysis

### **2. AI Analysis Layer** (`src/ai/`)
- Multi-timeframe technical analysis
- AI-powered market condition detection
- Consensus recommendation generation

### **3. Decision Layer** (`src/decision/`)
- Risk management and position sizing
- Trade approval/rejection logic
- Enhanced Excel trade recording

### **4. Notification Layer** (`src/notifications/`)
- Telegram and email notifications
- Trade alerts and summaries
- Error reporting

### **5. Technical Indicators** (`technicals/`)
- RSI, MACD, Bollinger Bands, ATR
- Candlestick pattern recognition
- Support/Resistance calculations

## 🧪 Testing

### **Run All Tests**
```bash
python run_comprehensive_tests.py
```

### **Test Specific Components**
```bash
# Test API credentials
python test_api_credentials.py

# Test enhanced recorder
cd trading_bot
python test_enhanced_recorder.py

# Test notifications
python test_notifications.py
```

### **Performance Testing**
```bash
python tests/test_performance.py
```

## 📚 Documentation

### **Setup Guides**
- [API Setup Guide](API_SETUP_README.md) - OANDA and OpenAI setup
- [Testing Guide](TESTING_README.md) - Comprehensive testing instructions

### **Component Documentation**
- [Enhanced Recorder](trading_bot/ENHANCED_RECORDER_README.md) - Trade recording system
- [Integration Analysis](integration_analysis.md) - System integration details

### **Configuration Files**
- `config.env` - Environment variables
- `trading_bot/config/trading_config.yaml` - Trading parameters

## 🔄 Usage Examples

### **Start Trading Bot**
```bash
# From project root (recommended)
python start_bot.py

# Or from trading_bot directory
cd trading_bot
python main.py
```

### **Test API Credentials**
```bash
python test_api_credentials.py
```

### **Run Data Collection**
```bash
python run_scraping.py
```

### **Run API Tests**
```bash
python run_api_tests.py
```

## 📊 Monitoring

### **Logs**
- Trading logs: `trading_bot/logs/trading_bot.log`
- Trade records: `trading_bot/logs/trades/complete_trading_records.xlsx`

### **Notifications**
- Telegram: Real-time trade alerts
- Email: Daily summaries and error reports

### **Performance Metrics**
- Win rate and profit factor
- Maximum drawdown
- Sharpe ratio and risk metrics

## 🤝 Contributing

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt

# Run code quality checks
black .
flake8 .
mypy .

# Run tests
pytest tests/
```

### **Code Style**
- Use Black for code formatting
- Follow PEP 8 guidelines
- Add type hints to all functions
- Write comprehensive docstrings

## ⚠️ Disclaimer

This trading bot is for educational and research purposes. Trading forex involves substantial risk of loss. Always:
- Test thoroughly in demo accounts
- Start with small position sizes
- Monitor the bot continuously
- Understand the risks involved

## 📞 Support

For issues and questions:
1. Check the logs in `trading_bot/logs/`
2. Review the configuration files
3. Run the test scripts
4. Check the documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Trading! 🚀**

