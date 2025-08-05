# Market Adaptive Trading Bot

A sophisticated algorithmic trading system that adapts to different market conditions using AI analysis and real-time notifications.

## 🏗️ System Architecture

### Core Components

1. **Data Layer** - Real-time market data collection and storage
2. **AI Analysis Layer** - OpenAI-powered market condition analysis and trade recommendations
3. **Decision Layer** - Risk management and trade validation
4. **Notification Layer** - Multi-channel trade alerts (Telegram, Email)
5. **Trade Interaction Handler** - User response processing
6. **Execution Layer** - Automated trade execution (optional)

### Market Conditions Supported

- **News/Reactionary Market** - High volatility during news events
- **Reversal Market** - Trend turning points and reversals
- **Breakout Market** - Price breaking through key levels
- **Ranging Market** - Sideways consolidation periods

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the system
python main.py
```

## 📊 Features

- **Real-time market analysis** with AI-powered insights
- **Multi-timeframe analysis** (M1, M5, M15, H1)
- **Automated risk management** with position sizing
- **Instant notifications** via Telegram and Email
- **Interactive trade management** with accept/edit/deny commands
- **Comprehensive logging** and performance tracking

## 🔧 Configuration

See `config/trading_config.yaml` for strategy parameters and risk settings. 