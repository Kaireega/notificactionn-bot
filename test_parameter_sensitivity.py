#!/usr/bin/env python3
"""
Test different parameter combinations to see if we can generate trades.
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


def load_test_dataset() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load a test dataset."""
    
    print("📊 Loading test dataset...")
    
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
                    
                    # Take the last 2000 candles for testing
                    df = df.tail(2000)
                    
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


async def test_parameter_combinations():
    """Test different parameter combinations."""
    
    print("🚀 Parameter Sensitivity Test")
    print("=" * 60)
    
    # Load configuration and data
    config = Config()
    historical_data = load_test_dataset()
    
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
    
    # Define parameter combinations to test
    parameter_sets = [
        {
            'name': 'ULTRA LOOSE - Any Signal',
            'params': {
                'rsi_oversold': 50,  # Very loose
                'rsi_overbought': 50,  # Very loose
                'risk_percentage': 10.0,  # High risk
                'macd_signal_threshold': 0.00000001,  # Extremely sensitive
                'bollinger_threshold': 0.0001,  # Extremely sensitive
                'atr_multiplier': 0.5,  # Very tight stops
                'min_signal_strength': 0.01  # Extremely lenient
            }
        },
        {
            'name': 'VERY LOOSE - Most Signals',
            'params': {
                'rsi_oversold': 45,
                'rsi_overbought': 55,
                'risk_percentage': 5.0,
                'macd_signal_threshold': 0.000001,
                'bollinger_threshold': 0.001,
                'atr_multiplier': 1.0,
                'min_signal_strength': 0.05
            }
        },
        {
            'name': 'LOOSE - Many Signals',
            'params': {
                'rsi_oversold': 40,
                'rsi_overbought': 60,
                'risk_percentage': 3.0,
                'macd_signal_threshold': 0.00001,
                'bollinger_threshold': 0.01,
                'atr_multiplier': 1.5,
                'min_signal_strength': 0.1
            }
        },
        {
            'name': 'NORMAL - Balanced',
            'params': {
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'risk_percentage': 2.0,
                'macd_signal_threshold': 0.0001,
                'bollinger_threshold': 0.1,
                'atr_multiplier': 2.0,
                'min_signal_strength': 0.3
            }
        },
        {
            'name': 'STRICT - Few Signals',
            'params': {
                'rsi_oversold': 25,
                'rsi_overbought': 75,
                'risk_percentage': 1.0,
                'macd_signal_threshold': 0.001,
                'bollinger_threshold': 0.5,
                'atr_multiplier': 3.0,
                'min_signal_strength': 0.5
            }
        },
        {
            'name': 'VERY STRICT - Rare Signals',
            'params': {
                'rsi_oversold': 20,
                'rsi_overbought': 80,
                'risk_percentage': 0.5,
                'macd_signal_threshold': 0.01,
                'bollinger_threshold': 1.0,
                'atr_multiplier': 4.0,
                'min_signal_strength': 0.7
            }
        }
    ]
    
    # Test each parameter set
    results = []
    
    for i, param_set in enumerate(parameter_sets, 1):
        print(f"\n🧪 Test {i}/6: {param_set['name']}")
        print("-" * 40)
        
        try:
            # Create backtest engine
            backtest_engine = BacktestEngine(config)
            
            # Run backtest
            result = await backtest_engine.run_backtest(
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
                parameters=param_set['params']
            )
            
            # Store results
            test_result = {
                'name': param_set['name'],
                'trades': result.total_trades,
                'return': result.total_return,
                'win_rate': result.win_rate,
                'final_balance': result.final_balance
            }
            results.append(test_result)
            
            print(f"   📈 Trades: {result.total_trades}")
            print(f"   📊 Return: {result.total_return:.2%}")
            print(f"   🎯 Win Rate: {result.win_rate:.2%}")
            print(f"   💰 Final Balance: ${result.final_balance:,.2f}")
            
            if result.total_trades > 0:
                print(f"   ✅ SUCCESS: Generated {result.total_trades} trades!")
            else:
                print(f"   ❌ No trades generated")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'name': param_set['name'],
                'trades': 0,
                'return': 0,
                'win_rate': 0,
                'final_balance': 10000,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PARAMETER SENSITIVITY SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get('trades', 0) > 0]
    
    if successful_tests:
        print(f"✅ SUCCESS: {len(successful_tests)} parameter sets generated trades!")
        print("\n🎯 Best performing parameter sets:")
        
        # Sort by number of trades
        successful_tests.sort(key=lambda x: x['trades'], reverse=True)
        
        for i, result in enumerate(successful_tests[:3], 1):
            print(f"\n{i}. {result['name']}")
            print(f"   📈 Trades: {result['trades']}")
            print(f"   📊 Return: {result['return']:.2%}")
            print(f"   🎯 Win Rate: {result['win_rate']:.2%}")
            print(f"   💰 Final Balance: ${result['final_balance']:,.2f}")
    else:
        print("❌ NO TRADES GENERATED with any parameter set")
        print("\n🔍 This suggests there might be an issue with:")
        print("   - Technical analysis signal generation")
        print("   - Data format or quality")
        print("   - Risk management blocking all trades")
        print("   - Market conditions not meeting criteria")
    
    print("\n" + "=" * 60)


async def main():
    """Main function."""
    try:
        await test_parameter_combinations()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
