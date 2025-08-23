#!/usr/bin/env python3
"""
Comprehensive test to debug the backtesting process step by step.
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
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer


def create_test_data():
    """Create test data."""
    print("📊 Creating test data...")
    
    candles = []
    base_price = 1.1000
    
    # Create extreme price movements
    for i in range(50):
        if i < 25:
            # First half: extreme downtrend
            price_change = -0.003 - (i * 0.0003)
        else:
            # Second half: extreme uptrend
            price_change = 0.003 + ((i - 25) * 0.0003)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(50-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.001)),
            low=Decimal(str(current_price - 0.001)),
            close=Decimal(str(current_price + price_change * 0.3)),
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


async def test_backtest_comprehensive():
    """Test backtesting comprehensively."""
    
    print("🔧 Testing Backtesting Comprehensively...")
    
    # Load configuration
    config = Config()
    
    # Create test data
    historical_data = create_test_data()
    
    # Test 1: Check technical analysis
    print("\n🔧 Test 1: Technical Analysis")
    technical_analyzer = TechnicalAnalyzer()
    candles = historical_data["EUR_USD"][TimeFrame.M5]
    indicators = technical_analyzer.calculate_indicators(candles)
    print(f"   📊 RSI: {indicators.rsi}")
    print(f"   📊 MACD: {indicators.macd}")
    print(f"   📊 ATR: {indicators.atr}")
    
    # Test 2: Check signal generation
    print("\n🔧 Test 2: Signal Generation")
    from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
    technical_layer = TechnicalAnalysisLayer(config)
    
    # Apply very lenient parameters
    technical_layer.rsi_oversold = 45
    technical_layer.rsi_overbought = 55
    technical_layer.macd_signal_threshold = 0.000001
    technical_layer.bollinger_threshold = 0.005
    technical_layer.min_signal_strength = 0.1
    
    # Create market context
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        volatility=Decimal('0.001'),
        trend_strength=Decimal('0.0'),
        news_sentiment=Decimal('0.0')
    )
    
    # Test signal analysis
    signal_analysis = technical_layer._analyze_technical_signals(indicators, market_context)
    print(f"   📊 Has signal: {signal_analysis['has_signal']}")
    print(f"   📊 Overall signal: {signal_analysis['overall_signal']}")
    print(f"   📊 Signal strength: {signal_analysis['signal_strength']}")
    print(f"   📊 Reasoning: {signal_analysis['reasoning']}")
    
    # Test 3: Check backtest engine data preparation
    print("\n🔧 Test 3: Backtest Engine Data Preparation")
    backtest_engine = BacktestEngine(config)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=2)
    
    prepared_data = backtest_engine._prepare_historical_data(historical_data, start_date, end_date)
    print(f"   📊 Prepared data timestamps: {len(prepared_data)}")
    
    if prepared_data:
        first_timestamp = list(prepared_data.keys())[0]
        first_data = prepared_data[first_timestamp]
        print(f"   �� First timestamp: {first_timestamp}")
        print(f"   📊 First data pairs: {list(first_data.keys())}")
        for pair, timeframes in first_data.items():
            for timeframe, candles in timeframes.items():
                print(f"   📊 {pair} {timeframe.value}: {len(candles)} candles")
    
    # Test 4: Check parameter application
    print("\n🔧 Test 4: Parameter Application")
    test_parameters = {
        'rsi_oversold': 45,
        'rsi_overbought': 55,
        'macd_signal_threshold': 0.000001,
        'bollinger_threshold': 0.005,
        'min_signal_strength': 0.1,
        'risk_percentage': 2.0
    }
    
    backtest_engine._apply_parameters(test_parameters)
    print(f"   📊 RSI oversold: {backtest_engine.technical_layer.rsi_oversold}")
    print(f"   📊 RSI overbought: {backtest_engine.technical_layer.rsi_overbought}")
    print(f"   📊 Min signal strength: {backtest_engine.technical_layer.min_signal_strength}")
    
    # Test 5: Check single timestamp processing
    print("\n🔧 Test 5: Single Timestamp Processing")
    if prepared_data:
        first_timestamp = list(prepared_data.keys())[0]
        first_data = prepared_data[first_timestamp]
        
        try:
            await backtest_engine._process_timestamp(first_timestamp, first_data)
            print(f"   ✅ Single timestamp processing completed")
            print(f"   📊 Open positions: {len(backtest_engine.open_positions)}")
        except Exception as e:
            print(f"   ❌ Error in single timestamp processing: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main function."""
    try:
        await test_backtest_comprehensive()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
