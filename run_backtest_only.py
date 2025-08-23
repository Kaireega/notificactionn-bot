#!/usr/bin/env python3
"""
Backtester that only loads existing data and runs backtesting (no data collection).
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


def load_existing_historical_data() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load existing historical data from pickle files."""
    
    print("📊 Loading existing historical data from pickle files...")
    
    # Load the existing data
    historical_data = {}
    pairs = ["EUR_USD", "USD_JPY", "GBP_JPY"]
    timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4]
    
    for pair in pairs:
        historical_data[pair] = {}
        
        for timeframe in timeframes:
            try:
                # Load from local pickle file
                file_path = f"data/{pair}_{timeframe.value}.pkl"
                if os.path.exists(file_path):
                    df = pd.read_pickle(file_path)
                    
                    # Convert to CandleData objects
                    candles = []
                    for _, row in df.iterrows():
                        # Ensure timestamp is timezone-aware
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
                    print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value} from {file_path}")
                    
                else:
                    print(f"   ⚠️ File not found: {file_path}")
                    historical_data[pair][timeframe] = []
                    
            except Exception as e:
                print(f"   ❌ Error loading data for {pair} {timeframe.value}: {e}")
                historical_data[pair][timeframe] = []
    
    return historical_data


async def run_backtest_only():
    """Run backtest with existing data (no data collection)."""
    
    print("🚀 Starting Backtest with Existing Data")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    
    # Load existing historical data
    historical_data = load_existing_historical_data()
    
    # Check if we have data
    total_candles = 0
    for pair, timeframes in historical_data.items():
        for timeframe, candles in timeframes.items():
            total_candles += len(candles)
    
    if total_candles == 0:
        print("❌ No historical data available. Please run data collection first.")
        return
    
    print(f"📊 Total candles loaded: {total_candles}")
    
    # Define backtest period (last 2 years of data)
    end_date = datetime(2025, 6, 1, tzinfo=timezone.utc)  # Make timezone-aware
    start_date = end_date - timedelta(days=730)  # Last 2 years
    
    # Create backtest engine
    backtest_engine = BacktestEngine(config)
    
    # Run backtest with aggressive parameters to generate more trades
    print("🔄 Running backtest with aggressive parameters...")
    result = await backtest_engine.run_backtest(
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        parameters={
            'rsi_oversold': 40,  # Very lenient
            'rsi_overbought': 60,  # Very lenient
            'risk_percentage': 2.0,
            'macd_signal_threshold': 0.000001,  # Very sensitive
            'bollinger_threshold': 0.01,  # Very sensitive
            'atr_multiplier': 2.0,
            'min_signal_strength': 0.1  # Very lenient
        }
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 BACKTEST RESULTS")
    print("=" * 60)
    print(f"💰 Initial Balance: ${result.initial_balance:,.2f}")
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
    
    if result.total_trades > 0:
        print("\n" + "=" * 60)
        print("✅ Backtest completed successfully with trades!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️ Backtest completed but no trades were generated.")
        print("   This may indicate the market conditions didn't meet signal criteria.")
        print("=" * 60)


async def main():
    """Main function."""
    try:
        await run_backtest_only()
    except KeyboardInterrupt:
        print("\n🛑 Backtest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
