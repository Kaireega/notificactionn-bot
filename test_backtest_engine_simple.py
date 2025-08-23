#!/usr/bin/env python3
"""
Simple test to verify backtest engine is processing data correctly.
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
    """Load a very small dataset for testing."""
    
    print("📊 Loading small dataset...")
    
    # Load EUR_USD M5 data
    historical_data = {}
    pairs = ["EUR_USD"]
    timeframes = [TimeFrame.M5]
    
    for pair in pairs:
        historical_data[pair] = {}
        
        for timeframe in timeframes:
            try:
                file_path = f"data/{pair}_{timeframe.value}.pkl"
                if os.path.exists(file_path):
                    df = pd.read_pickle(file_path)
                    
                    # Take just the last 50 candles for quick testing
                    df = df.tail(50)
                    
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


async def test_backtest_engine():
    """Test the backtest engine with a small dataset."""
    
    print("🔍 Testing Backtest Engine")
    print("=" * 50)
    
    # Load configuration and data
    config = Config()
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
    start_date = all_candles[0].timestamp
    end_date = all_candles[-1].timestamp
    
    print(f"📅 Testing period: {start_date} to {end_date}")
    print(f"📊 Total candles: {len(all_candles)}")
    
    # Use ultra-loose parameters
    parameters = {
        'rsi_oversold': 50,  # Very loose
        'rsi_overbought': 50,  # Very loose
        'risk_percentage': 10.0,  # High risk
        'macd_signal_threshold': 0.00000001,  # Extremely sensitive
        'bollinger_threshold': 0.0001,  # Extremely sensitive
        'atr_multiplier': 0.5,  # Very tight stops
        'min_signal_strength': 0.01  # Extremely lenient
    }
    
    print(f"\n🧪 Running backtest with ultra-loose parameters...")
    
    try:
        # Create backtest engine
        backtest_engine = BacktestEngine(config)
        
        # Run backtest
        result = await backtest_engine.run_backtest(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        
        print(f"\n📊 Backtest Results:")
        print(f"   📈 Trades: {result.total_trades}")
        print(f"   📊 Return: {result.total_return:.2%}")
        print(f"   🎯 Win Rate: {result.win_rate:.2%}")
        print(f"   💰 Final Balance: ${result.final_balance:,.2f}")
        
        if result.total_trades > 0:
            print(f"   ✅ SUCCESS: Generated {result.total_trades} trades!")
        else:
            print(f"   ❌ No trades generated")
            print(f"   🔍 This suggests the backtest engine is not processing data correctly")
            
    except Exception as e:
        print(f"   ❌ Error in backtest: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 BACKTEST ENGINE TEST SUMMARY")
    print("=" * 50)


async def main():
    """Main function."""
    try:
        await test_backtest_engine()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
