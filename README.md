# Production Trading Bot

## Quick Start

1. **Configure your credentials in `config.env`:**
   ```bash
   # Required
   OANDA_API_KEY=your_actual_oanda_api_key
   OANDA_ACCOUNT_ID=your_actual_oanda_account_id
   
   # Optional (for AI analysis)
   OPENAI_API_KEY=your_openai_api_key
   ```

2. **Start the bot:**
   ```bash
   python run_bot.py
   ```

## Configuration

The bot uses the original configuration from the main branch with:
- **Technical Analysis**: RSI, MACD, Bollinger Bands, ATR
- **AI Analysis**: GPT-4 integration (optional)
- **Risk Management**: Position sizing, stop-loss, take-profit
- **Multi-timeframe Analysis**: M1, M5, M15 timeframes

## Safety Features

- Live trading disabled by default (`LIVE_TRADE_ENABLED=False`)
- Comprehensive error handling
- Risk management built-in
- Graceful shutdown

## To Enable Live Trading

Edit `config.env` and set:
```
LIVE_TRADE_ENABLED=True
```

**⚠️ Always test with paper trading first!**

