#!/usr/bin/env python3
"""
Test to debug parameter application in backtesting.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.backtest_engine import BacktestEngine
from trading_bot.src.core.models import TimeFrame, CandleData


def create_test_data():
    """Create test data."""
    print("📊 Creating test data...")
    
    candles = []
    base_price = 1.1000
    
    # Create data that should definitely trigger signals
    for i in range(50):
        # Create extreme price movements
        if i < 25:
            # First half: extreme downtrend
            price_change = -0.002 - (i * 0.0002)
        else:
            # Second half: extreme uptrend
            price_change = 0.002 + ((i - 25) * 0.0002)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(50-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.0005)),
            low=Decimal(str(current_price - 0.0005)),
            close=Decimal(str(current_price + price_change * 0.2)),
            volume=Decimal('1000')
        )
        candles.append(candle)
    
    print(f"   ✅ Created {len(candles)} test candles")
    
    historical_data = {
        "EUR_USD": {
            TimeFrame.M5: candles
        }
    }
    
    return historical_data


async def test_parameters():
    """Test parameter application."""
    
    print("🔧 Testing Parameter Application...")
    
    # Load configuration
    config = Config()
    
    # Create test data
    historical_data = create_test_data()
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Print initial parameters
    print(f"   📊 Initial technical layer parameters:")
    print(f"      RSI oversold: {backtest_engine.technical_layer.rsi_oversold}")
    print(f"      RSI overbought: {backtest_engine.technical_layer.rsi_overbought}")
    print(f"      MACD threshold: {backtest_engine.technical_layer.macd_signal_threshold}")
    print(f"      Bollinger threshold: {backtest_engine.technical_layer.bollinger_threshold}")
    print(f"      Min signal strength: {backtest_engine.technical_layer.min_signal_strength}")
    
    # Define test parameters
    test_parameters = {
        'rsi_oversold': 40,  # Very lenient
        'rsi_overbought': 60,  # Very lenient
        'macd_signal_threshold': 0.00001,  # Very sensitive
        'bollinger_threshold': 0.01,  # Very sensitive
        'min_signal_strength': 0.1,  # Very lenient
        'risk_percentage': 2.0
    }
    
    # Apply parameters
    backtest_engine._apply_parameters(test_parameters)
    
    # Print updated parameters
    print(f"   📊 Updated technical layer parameters:")
    print(f"      RSI oversold: {backtest_engine.technical_layer.rsi_oversold}")
    print(f"      RSI overbought: {backtest_engine.technical_layer.rsi_overbought}")
    print(f"      MACD threshold: {backtest_engine.technical_layer.macd_signal_threshold}")
    print(f"      Bollinger threshold: {backtest_engine.technical_layer.bollinger_threshold}")
    print(f"      Min signal strength: {backtest_engine.technical_layer.min_signal_strength}")
    
    # Test technical analysis directly
    print(f"   🔧 Testing technical analysis with updated parameters...")
    
    # Get the first pair and timeframe
    pair = "EUR_USD"
    timeframes = historical_data[pair]
    candles = timeframes[TimeFrame.M5]
    
    # Create market context
    from trading_bot.src.core.models import MarketContext, MarketCondition
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        volatility=Decimal('0.001'),
        trend_strength=Decimal('0.0'),
        news_sentiment=Decimal('0.0')
    )
    
    # Run technical analysis
    try:
        recommendation, indicators = await backtest_engine.technical_layer.analyze_multiple_timeframes(
            pair, timeframes, market_context
        )
        
        print(f"   ✅ Technical analysis completed")
        print(f"   📊 Recommendation: {recommendation}")
        print(f"   📈 Indicators: {indicators}")
        
        if recommendation:
            print(f"   🎯 Signal: {recommendation.signal}")
            print(f"   📊 Confidence: {recommendation.confidence}")
            print(f"   💰 Entry Price: {recommendation.entry_price}")
            print(f"   🛑 Stop Loss: {recommendation.stop_loss}")
            print(f"   🎯 Take Profit: {recommendation.take_profit}")
        else:
            print(f"   ❌ No recommendation generated")
        
        if indicators:
            print(f"   📊 RSI: {indicators.rsi}")
            print(f"   📊 MACD: {indicators.macd}")
            print(f"   📊 ATR: {indicators.atr}")
        
    except Exception as e:
        print(f"   ❌ Error in technical analysis: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function."""
    try:
        await test_parameters()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
