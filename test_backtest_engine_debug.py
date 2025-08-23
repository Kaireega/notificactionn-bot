#!/usr/bin/env python3
"""
Debug test for backtest engine to see what's happening.
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


def create_simple_test_data():
    """Create simple test data."""
    print("📊 Creating simple test data...")
    
    candles = []
    base_price = 1.1000
    
    # Create data that should definitely trigger signals
    for i in range(20):
        # Create extreme price movements
        if i < 10:
            # First half: extreme downtrend
            price_change = -0.003 - (i * 0.0003)
        else:
            # Second half: extreme uptrend
            price_change = 0.003 + ((i - 10) * 0.0003)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(20-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.0005)),
            low=Decimal(str(current_price - 0.0005)),
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


async def test_backtest_engine_debug():
    """Test backtest engine with debugging."""
    
    print("🔧 Testing Backtest Engine with Debugging...")
    
    # Load configuration
    config = Config()
    
    # Create test data
    historical_data = create_simple_test_data()
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Define backtest period
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=2)
    
    # Test data preparation
    print(f"   🔧 Testing data preparation...")
    prepared_data = backtest_engine._prepare_historical_data(historical_data, start_date, end_date)
    print(f"   �� Prepared data timestamps: {len(prepared_data)}")
    
    if prepared_data:
        first_timestamp = list(prepared_data.keys())[0]
        first_data = prepared_data[first_timestamp]
        print(f"   📊 First timestamp: {first_timestamp}")
        print(f"   📊 First data pairs: {list(first_data.keys())}")
        for pair, timeframes in first_data.items():
            for timeframe, candles in timeframes.items():
                print(f"   📊 {pair} {timeframe.value}: {len(candles)} candles")
    
    # Test parameter application
    print(f"   🔧 Testing parameter application...")
    test_parameters = {
        'rsi_oversold': 45,
        'rsi_overbought': 55,
        'macd_signal_threshold': 0.000001,
        'bollinger_threshold': 0.005,
        'min_signal_strength': 0.1,
        'risk_percentage': 2.0
    }
    
    backtest_engine._apply_parameters(test_parameters)
    print(f"   ✅ Parameters applied")
    print(f"   📊 RSI oversold: {backtest_engine.technical_layer.rsi_oversold}")
    print(f"   📊 RSI overbought: {backtest_engine.technical_layer.rsi_overbought}")
    print(f"   📊 Min signal strength: {backtest_engine.technical_layer.min_signal_strength}")
    
    # Test a single timestamp processing
    if prepared_data:
        print(f"   🔧 Testing single timestamp processing...")
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
        await test_backtest_engine_debug()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
