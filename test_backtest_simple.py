#!/usr/bin/env python3
"""
Simple backtest with a small dataset to debug the issue.
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
    """Create simple test data that should definitely generate signals."""
    print("📊 Creating simple test data...")
    
    candles = []
    base_price = 1.1000
    
    # Create very extreme price movements to trigger signals
    for i in range(30):
        if i < 15:
            # First half: extreme downtrend (should trigger oversold)
            price_change = -0.005 - (i * 0.0005)
        else:
            # Second half: extreme uptrend (should trigger overbought)
            price_change = 0.005 + ((i - 15) * 0.0005)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(30-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.001)),
            low=Decimal(str(current_price - 0.001)),
            close=Decimal(str(current_price + price_change * 0.5)),
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


async def test_simple_backtest():
    """Test simple backtest."""
    
    print("🔧 Testing Simple Backtest...")
    
    # Load configuration
    config = Config()
    
    # Create test data
    historical_data = create_simple_test_data()
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Define backtest period
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=1)
    
    # Run backtest with very lenient parameters
    print("🔄 Running simple backtest...")
    result = await backtest_engine.run_backtest(
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        parameters={
            'rsi_oversold': 45,  # Very lenient
            'rsi_overbought': 55,  # Very lenient
            'macd_signal_threshold': 0.000001,  # Very sensitive
            'bollinger_threshold': 0.005,  # Very sensitive
            'min_signal_strength': 0.1,  # Very lenient
            'risk_percentage': 2.0
        }
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 SIMPLE BACKTEST RESULTS")
    print("=" * 60)
    print(f"💰 Initial Balance: ${result.initial_balance:,.2f}")
    print(f"💰 Final Balance: ${result.final_balance:,.2f}")
    print(f"📊 Total Return: {result.total_return:.2%}")
    print(f"📈 Total Trades: {result.total_trades}")
    print(f"✅ Winning Trades: {result.winning_trades}")
    print(f"❌ Losing Trades: {result.losing_trades}")
    print(f"🎯 Win Rate: {result.win_rate:.2%}")
    
    if result.total_trades > 0:
        print("✅ Backtest generated trades successfully!")
    else:
        print("❌ Backtest did not generate any trades")


async def main():
    """Main function."""
    try:
        await test_simple_backtest()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
