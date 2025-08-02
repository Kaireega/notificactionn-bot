# 📁 Project Structure Documentation

## 🏗️ Complete Project Overview

```
forex-trading-bot/
├── 🤖 market_adaptive_bot/          # Main trading bot application
├── 📊 technicals/                   # Technical indicators and patterns
├── 🔌 api/                          # API integrations
├── 📊 data/                         # Data management
├── 🧪 tests/                        # Test suites
├── 📚 docs/                         # Documentation
├── 🔧 scripts/                      # Utility scripts
└── 📋 config/                       # Configuration files
```

## 🤖 Market Adaptive Bot (`market_adaptive_bot/`)

The main trading bot application with AI-powered analysis and risk management.

### **Core Structure**
```
market_adaptive_bot/
├── 📊 src/                          # Source code
│   ├── 🧠 ai/                       # AI analysis layer
│   │   ├── ai_analysis_layer.py     # Main AI analysis
│   │   ├── technical_analyzer.py    # Technical indicators (uses technicals/)
│   │   └── multi_timeframe_analyzer.py # Multi-timeframe analysis
│   ├── 📈 data/                     # Data collection layer
│   │   └── data_layer.py            # Data management
│   ├── 🎯 decision/                 # Decision making layer
│   │   ├── decision_layer.py        # Main decision logic
│   │   ├── risk_manager.py          # Risk management
│   │   ├── performance_tracker.py   # Performance tracking
│   │   └── enhanced_excel_trade_recorder.py # Trade recording
│   ├── 📱 notifications/            # Notification layer
│   │   ├── notification_layer.py    # Main notifications
│   │   └── chart_generator.py       # Chart generation
│   ├── 🔧 utils/                    # Utilities
│   │   ├── config.py                # Configuration management
│   │   └── logger.py                # Logging utilities
│   └── 🧩 core/                     # Core models
│       └── models.py                # Data models
├── 📋 config/                       # Configuration
│   └── trading_config.yaml          # Trading parameters
├── 📊 logs/                         # Logs and records
│   └── trades/                      # Trade records
├── 🧪 tests/                        # Bot-specific tests
├── 📄 main.py                       # Main entry point
├── 📋 requirements.txt               # Dependencies
├── 📖 README.md                     # Bot documentation
└── 🔧 setup_and_start.py            # Setup script
```

### **Key Components**

#### **🧠 AI Analysis Layer** (`src/ai/`)
- **`ai_analysis_layer.py`**: Main AI analysis using OpenAI
- **`technical_analyzer.py`**: Technical indicators (uses `technicals/`)
- **`multi_timeframe_analyzer.py`**: Multi-timeframe consensus analysis

#### **📈 Data Layer** (`src/data/`)
- **`data_layer.py`**: Real-time data collection and management

#### **🎯 Decision Layer** (`src/decision/`)
- **`decision_layer.py`**: Main decision logic and trade approval
- **`risk_manager.py`**: Risk management and position sizing
- **`performance_tracker.py`**: Performance metrics tracking
- **`enhanced_excel_trade_recorder.py`**: Comprehensive trade recording

#### **📱 Notification Layer** (`src/notifications/`)
- **`notification_layer.py`**: Telegram and email notifications
- **`chart_generator.py`**: Chart generation for notifications

## 📊 Technical Indicators (`technicals/`)

Existing technical analysis library with proven implementations.

### **Structure**
```
technicals/
├── 📊 indicators.py                 # Technical indicators
│   ├── RSI()                       # Relative Strength Index
│   ├── MACD()                      # Moving Average Convergence Divergence
│   ├── BollingerBands()            # Bollinger Bands
│   ├── ATR()                       # Average True Range
│   └── KeltnerChannels()           # Keltner Channels
└── 📈 patterns.py                  # Candlestick patterns
    ├── apply_candle_props()        # Candle properties
    ├── set_candle_patterns()       # Pattern detection
    └── Various pattern functions   # Doji, Hammer, etc.
```

### **Indicators Available**
- **RSI**: Relative Strength Index with exponential weighting
- **MACD**: MACD with signal line and histogram
- **Bollinger Bands**: Upper, middle, lower bands using typical price
- **ATR**: Average True Range for volatility measurement
- **Keltner Channels**: Volatility-based channels

### **Patterns Available**
- **Doji**: Neutral candlestick patterns
- **Hammer**: Reversal patterns
- **Engulfing**: Bullish/Bearish engulfing patterns
- **Morning/Evening Star**: Reversal patterns
- **Three Soldiers/Crows**: Continuation patterns

## 🔌 API Integrations (`api/`)

External API integrations for data and trading.

### **Structure**
```
api/
├── 📊 oanda_api.py                 # OANDA forex API
├── 🌐 web_options.py               # Web scraping utilities
└── 🔗 unified_api.py               # Unified API interface
```

### **APIs Integrated**
- **OANDA API**: Real-time forex data and trading
- **OpenAI API**: AI analysis and recommendations
- **Telegram API**: Notifications and alerts

## 📊 Data Management (`data/`)

Historical data and data management utilities.

### **Structure**
```
data/
├── 📈 historical/                   # Historical data storage
├── 📋 instruments.json              # Instrument definitions
└── 📊 data_collection/              # Data collection scripts
```

## 🧪 Testing (`tests/`)

Comprehensive test suites for all components.

### **Structure**
```
tests/
├── 🧪 unit/                        # Unit tests
├── 🔗 integration/                  # Integration tests
├── 📊 performance/                  # Performance tests
├── 🧪 test_edge_cases.py           # Edge case testing
├── 🔗 test_integration.py           # Integration testing
└── 📊 test_performance.py           # Performance testing
```

### **Test Categories**
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Load and stress testing
- **Edge Cases**: Boundary condition testing

## 📚 Documentation (`docs/`)

Comprehensive documentation for the project.

### **Structure**
```
docs/
├── 📖 setup/                        # Setup guides
├── 🔧 api/                          # API documentation
├── 📊 technical/                    # Technical documentation
└── 📋 user/                         # User guides
```

## 🔧 Scripts and Utilities

### **Main Scripts**
- **`main.py`**: Main trading bot entry point
- **`cleanup.py`**: Codebase cleanup and organization
- **`run_comprehensive_tests.py`**: Full test suite execution
- **`test_api_credentials.py`**: API credential validation

### **Configuration Files**
- **`requirements.txt`**: Comprehensive dependency list
- **`config.env`**: Environment variables
- **`.gitignore`**: Git ignore patterns
- **`README.md`**: Main project documentation

## 📋 Configuration Management

### **Environment Variables** (`config.env`)
```env
# OANDA API Configuration
OANDA_API_KEY=your_api_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_URL=https://api-fxpractice.oanda.com/v3

# OpenAI API
OPENAI_API_KEY=your_openai_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Email (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_password
```

### **Trading Configuration** (`market_adaptive_bot/config/trading_config.yaml`)
```yaml
trading:
  pairs: ["EUR_USD", "USD_JPY", "GBP_JPY"]
  risk_percentage: 1.0
  max_daily_loss: 5.0
  max_trades_per_day: 10

ai:
  confidence_threshold: 0.6
  timeframes: ["M5", "M15", "H1"]

risk_management:
  correlation_threshold: 0.7
  volatility_threshold: 0.02
  market_hours_only: true
```

## 🔄 Data Flow

### **1. Data Collection**
```
OANDA API → Data Layer → Market Context
```

### **2. Analysis**
```
Market Data → Technical Analyzer → AI Analysis → Multi-timeframe Analysis
```

### **3. Decision Making**
```
AI Recommendations → Risk Manager → Decision Layer → Trade Approval
```

### **4. Execution**
```
Trade Decision → Notification Layer → Trade Recording → Performance Tracking
```

## 📊 Logging and Monitoring

### **Log Files**
- **`market_adaptive_bot/logs/trading_bot.log`**: Main trading logs
- **`market_adaptive_bot/logs/trades/complete_trading_records.xlsx`**: Trade records

### **Monitoring**
- **Real-time notifications**: Telegram and email alerts
- **Performance metrics**: Win rate, profit factor, drawdown
- **System health**: Error logging and status updates

## 🚀 Deployment

### **Development Setup**
```bash
# Clone and setup
git clone <repository>
cd forex-trading-bot
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp market_adaptive_bot/env_example.txt config.env
# Edit config.env with your API keys

# Run tests
python test_api_credentials.py

# Start the bot
cd market_adaptive_bot
python main.py
```

### **Production Considerations**
- Use process manager (supervisor, systemd)
- Set up monitoring and alerting
- Configure proper logging
- Implement backup strategies
- Use secure credential management

## 🔧 Maintenance

### **Regular Tasks**
- Monitor log files for errors
- Review trade performance metrics
- Update API credentials as needed
- Backup trade records and configurations
- Update dependencies regularly

### **Troubleshooting**
- Check API credentials and connectivity
- Review error logs in `market_adaptive_bot/logs/`
- Validate configuration files
- Run test scripts to isolate issues
- Check system resources and performance

---

This structure provides a comprehensive, modular, and maintainable forex trading bot with clear separation of concerns and extensive documentation. 