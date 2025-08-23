#!/usr/bin/env python3
"""
Quick test to verify backtesting components are working.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.backtest_engine import BacktestEngine, BacktestResult
from trading_bot.src.core.models import TimeFrame, CandleData


def load_small_dataset() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load a small dataset for quick testing."""
    
    print("📊 Loading small dataset for quick testing...")
    
    # Load just EUR_USD M5 data for a short period
    historical_data = {}
    pairs = ["EUR_USD"]  # Just one pair
    timeframes = [TimeFrame.M5]  # Just one timeframe
    
    for pair in pairs:
        historical_data[pair] = {}
        
        for timeframe in timeframes:
            try:
                file_path = f"data/{pair}_{timeframe.value}.pkl"
                if os.path.exists(file_path):
                    df = pd.read_pickle(file_path)
                    
                    # Take only the last 1000 candles for quick testing
                    df = df.tail(1000)
                    
                    candles = []
                    for _, row in df.iterrows():
                        timestamp = row["time"].to_pydatetime()
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                        
                        candle = CandleData(
                            timestamp=timestamp,
                            open=Decimal(str(row["mid_o"])),
                            high=Decimal(str(row["mid_h"])),
                            low=Decimal(str(row["mid_l"])),
                            close=Decimal(str(row["mid_c"])),
                            volume=Decimal(str(row.get("volume", 1000)))
                        )
                        candles.append(candle)
                    
                    historical_data[pair][timeframe] = candles
                    print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value}")
                    
                else:
                    print(f"   ❌ File not found: {file_path}")
                    return {}
                    
            except Exception as e:
                print(f"   ❌ Error loading data: {e}")
                return {}
    
    return historical_data


async def test_quick_backtest():
    """Run a quick backtest with minimal data."""
    
    print("🚀 Quick Backtest Test")
    print("=" * 40)
    
    # Load configuration
    config = Config()
    
    # Load small dataset
    historical_data = load_small_dataset()
    
    if not historical_data:
        print("❌ No data available for testing.")
        return
    
    # Get date range from the data
    all_candles = []
    for pair, timeframes in historical_data.items():
        for timeframe, candles in timeframes.items():
            all_candles.extend(candles)
    
    if not all_candles:
        print("❌ No candles found.")
        return
    
    # Sort by timestamp
    all_candles.sort(key=lambda x: x.timestamp)
    
    # Use the last 100 candles for testing
    test_candles = all_candles[-100:]
    start_date = test_candles[0].timestamp
    end_date = test_candles[-1].timestamp
    
    print(f"📅 Testing period: {start_date} to {end_date}")
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Run backtest with very aggressive parameters
    print("🔄 Running quick backtest...")
    result = await backtest_engine.run_backtest(
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        parameters={
            'rsi_oversold': 45,  # Very lenient
            'rsi_overbought': 55,  # Very lenient
            'risk_percentage': 5.0,  # Higher risk
            'macd_signal_threshold': 0.0000001,  # Extremely sensitive
            'bollinger_threshold': 0.001,  # Extremely sensitive
            'atr_multiplier': 1.0,  # Smaller stops
            'min_signal_strength': 0.05  # Very lenient
        }
    )
    
    # Print results
    print("\n" + "=" * 40)
    print("📊 QUICK TEST RESULTS")
    print("=" * 40)
    print(f"📈 Total Trades: {result.total_trades}")
    print(f"💰 Final Balance: ${result.final_balance:,.2f}")
    print(f"📊 Total Return: {result.total_return:.2%}")
    
    if result.total_trades > 0:
        print("✅ SUCCESS: Trades were generated!")
    else:
        print("❌ ISSUE: No trades generated - need to debug further")


async def main():
    """Main function."""
    try:
        await test_quick_backtest()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
