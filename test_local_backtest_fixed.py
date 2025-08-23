#!/usr/bin/env python3
"""
Test script to run backtesting with local historical data (fixed version).
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
from trading_bot.src.backtesting.backtest_engine import BacktestEngine, BacktestResult
from trading_bot.src.core.models import TimeFrame, CandleData


def load_historical_data_from_pickle() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load historical data from local pickle files for backtesting."""
    
    print("📊 Loading historical data from local pickle files...")
    
    # Use a date range that's within the available data (data ends at 2025-05-30)
    end_date = datetime(2025, 5, 30)  # Use the end date from the data
    start_date = end_date - timedelta(days=30)  # Last 30 days of available data
    
    historical_data = {}
    # Use only available pairs
    pairs = ["EUR_USD", "USD_JPY"]  # Removed GBP_USD since files don't exist
    timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
    
    for pair in pairs:
        historical_data[pair] = {}
        
        for timeframe in timeframes:
            try:
                # Load from local pickle file
                file_path = f"data/{pair}_{timeframe.value}.pkl"
                if os.path.exists(file_path):
                    df = pd.read_pickle(file_path)
                    
                    # Convert timezone-aware datetime to timezone-naive for comparison
                    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
                    start_date_naive = start_date.replace(tzinfo=None)
                    end_date_naive = end_date.replace(tzinfo=None)
                    
                    # Filter data by date range
                    mask = (df["time"] >= start_date_naive) & (df["time"] <= end_date_naive)
                    df_filtered = df.loc[mask]
                    
                    # Convert to CandleData objects
                    candles = []
                    for _, row in df_filtered.iterrows():
                        candle = CandleData(
                            timestamp=row["time"].to_pydatetime(),
                            open=Decimal(str(row["mid_o"])),
                            high=Decimal(str(row["mid_h"])),
                            low=Decimal(str(row["mid_l"])),
                            close=Decimal(str(row["mid_c"])),
                            volume=Decimal(str(row.get("volume", 1000)))
                        )
                        candles.append(candle)
                    
                    historical_data[pair][timeframe] = candles
                    print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value} from {file_path}")
                    
                else:
                    print(f"   ⚠️ File not found: {file_path}")
                    historical_data[pair][timeframe] = []
                    
            except Exception as e:
                print(f"   ❌ Error loading data for {pair} {timeframe.value}: {e}")
                historical_data[pair][timeframe] = []
    
    return historical_data


async def run_backtest_with_local_data():
    """Run backtest using local historical data."""
    
    print("🚀 Starting Backtest with Local Historical Data")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    
    # Load historical data
    historical_data = load_historical_data_from_pickle()
    
    # Check if we have data
    total_candles = 0
    for pair, timeframes in historical_data.items():
        for timeframe, candles in timeframes.items():
            total_candles += len(candles)
    
    if total_candles == 0:
        print("❌ No historical data available. Exiting.")
        return
    
    print(f"📊 Total candles loaded: {total_candles}")
    
    # Define backtest period (use the same dates as the data loading)
    end_date = datetime(2025, 5, 30)
    start_date = end_date - timedelta(days=30)
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Run backtest
    print("🔄 Running backtest...")
    result = await backtest_engine.run_backtest(
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        parameters={
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'risk_percentage': 2.0,
            'macd_signal_threshold': 0.0001,
            'bollinger_threshold': 0.1,
            'atr_multiplier': 2.0,
            'min_signal_strength': 0.5
        }
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 BACKTEST RESULTS")
    print("=" * 60)
    print(f"�� Initial Balance: ${result.initial_balance:,.2f}")
    print(f"💰 Final Balance: ${result.final_balance:,.2f}")
    print(f"📊 Total Return: {result.total_return:.2%}")
    print(f"📈 Total Trades: {result.total_trades}")
    print(f"✅ Winning Trades: {result.winning_trades}")
    print(f"❌ Losing Trades: {result.losing_trades}")
    print(f"🎯 Win Rate: {result.win_rate:.2%}")
    print(f"📊 Profit Factor: {result.profit_factor:.2f}")
    print(f"📉 Max Drawdown: {result.max_drawdown:.2%}")
    print(f"📈 Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"⏱️ Avg Trade Duration: {result.avg_trade_duration:.1f} minutes")
    print(f"🏆 Avg Win: ${result.avg_win:.2f}")
    print(f"💥 Avg Loss: ${result.avg_loss:.2f}")
    print(f"🔥 Consecutive Wins: {result.consecutive_wins}")
    print(f"💀 Consecutive Losses: {result.consecutive_losses}")
    
    print("\n" + "=" * 60)
    print("✅ Backtest completed successfully!")
    print("=" * 60)


async def main():
    """Main function."""
    try:
        await run_backtest_with_local_data()
    except KeyboardInterrupt:
        print("\n🛑 Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
