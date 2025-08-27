#!/usr/bin/env python3
"""
Example: Debug Backtesting System
Demonstrates how to use the comprehensive debug backtesting system.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from decimal import Decimal

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.debug_backtest_engine import DebugBacktestEngine, DebugBacktestResult
from trading_bot.src.core.models import TimeFrame, CandleData


class DebugBacktestingExample:
    """Example class demonstrating debug backtesting usage."""
    
    def __init__(self):
        self.config = Config()
    
    async def example_basic_usage(self):
        """Example 1: Basic debug backtesting usage."""
        print("🔍 Example 1: Basic Debug Backtesting")
        print("=" * 50)
        
        # Create debug engine with DETAILED logging
        debug_engine = DebugBacktestEngine(self.config, debug_level="DETAILED")
        
        # Create sample historical data
        historical_data = self._create_sample_data()
        
        # Define test parameters
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        parameters = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'risk_percentage': 1.0
        }
        
        print(f"Running backtest from {start_date} to {end_date}")
        print(f"Parameters: {parameters}")
        
        # Run debug backtest
        result = await debug_engine.run_backtest(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        
        # Print results
        self._print_basic_results(result)
        
        # Generate debug report
        report_file = debug_engine.generate_debug_report(result, "example_reports")
        print(f"\n📄 Debug report saved to: {report_file}")
        
        return result
    
    async def example_parameter_optimization(self):
        """Example 2: Debug backtesting with parameter optimization."""
        print("\n🔍 Example 2: Parameter Optimization with Debug")
        print("=" * 50)
        
        # Create debug engine with VERBOSE logging
        debug_engine = DebugBacktestEngine(self.config, debug_level="VERBOSE")
        
        # Create sample historical data
        historical_data = self._create_sample_data()
        
        # Define date range
        start_date = datetime.now(timezone.utc) - timedelta(days=14)
        end_date = datetime.now(timezone.utc)
        
        # Test different parameter sets
        parameter_sets = [
            {'rsi_oversold': 25, 'rsi_overbought': 75, 'risk_percentage': 1.0},
            {'rsi_oversold': 30, 'rsi_overbought': 70, 'risk_percentage': 1.5},
            {'rsi_oversold': 35, 'rsi_overbought': 65, 'risk_percentage': 2.0}
        ]
        
        results = []
        
        for i, params in enumerate(parameter_sets, 1):
            print(f"\nTesting parameter set {i}: {params}")
            
            result = await debug_engine.run_backtest(
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
                parameters=params
            )
            
            results.append((params, result))
            
            print(f"  Result: {result.total_trades} trades, {result.win_rate:.1f}% win rate, {result.total_return:+.2f}% return")
        
        # Find best performing parameters
        best_result = max(results, key=lambda x: x[1].total_return)
        print(f"\n🏆 Best performing parameters: {best_result[0]}")
        print(f"   Return: {best_result[1].total_return:+.2f}%")
        print(f"   Win Rate: {best_result[1].win_rate:.1f}%")
        
        return results
    
    async def example_performance_analysis(self):
        """Example 3: Detailed performance analysis."""
        print("\n🔍 Example 3: Performance Analysis")
        print("=" * 50)
        
        # Run a backtest first
        result = await self.example_basic_usage()
        
        if not result:
            print("❌ Cannot perform analysis without backtest result")
            return
        
        # Analyze performance
        print("\n📊 PERFORMANCE ANALYSIS:")
        print(f"Total Return: {result.total_return:+.2f}%")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Profit Factor: {result.profit_factor:.3f}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        
        # Signal analysis
        print(f"\n📡 SIGNAL ANALYSIS:")
        print(f"Total Signals Generated: {result.total_signals_generated}")
        print(f"Signals Acted Upon: {result.signals_acted_upon}")
        print(f"Signals Ignored: {result.signals_ignored}")
        
        if result.total_signals_generated > 0:
            efficiency = result.signals_acted_upon / result.total_signals_generated * 100
            print(f"Signal Efficiency: {efficiency:.1f}%")
        
        # Risk analysis
        print(f"\n⚠️ RISK ANALYSIS:")
        print(f"Risk Checks Passed: {result.risk_checks_passed}")
        print(f"Risk Checks Failed: {result.risk_checks_failed}")
        print(f"Max Consecutive Losses: {result.consecutive_losses}")
        
        # Performance timing
        print(f"\n⏱️ PERFORMANCE TIMING:")
        print(f"Technical Analysis: {result.technical_analysis_time:.3f}s")
        print(f"Decision Making: {result.decision_making_time:.3f}s")
        print(f"Execution: {result.execution_time:.3f}s")
        
        # Debug information
        print(f"\n🐛 DEBUG INFORMATION:")
        print(f"Debug Logs: {len(result.debug_logs)}")
        print(f"Error Logs: {len(result.error_logs)}")
        print(f"Warnings: {len(result.warnings)}")
        
        if result.error_logs:
            print(f"\n❌ ERRORS DETECTED:")
            for error in result.error_logs[-3:]:
                print(f"  {error}")
    
    def _create_sample_data(self) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Create sample historical data for examples."""
        print("   Creating sample historical data...")
        
        historical_data = {}
        pairs = ["EUR_USD", "GBP_USD"]
        timeframes = [TimeFrame.M5, TimeFrame.M15]
        
        # Create data for last 7 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        for pair in pairs:
            historical_data[pair] = {}
            
            for timeframe in timeframes:
                candles = self._generate_sample_candles(start_date, end_date, timeframe, pair)
                historical_data[pair][timeframe] = candles
                print(f"   ✅ Generated {len(candles)} candles for {pair} {timeframe.value}")
        
        return historical_data
    
    def _generate_sample_candles(self, start_date: datetime, end_date: datetime, 
                                timeframe: TimeFrame, pair: str) -> List[CandleData]:
        """Generate sample candle data."""
        import random
        
        candles = []
        current_time = start_date
        
        # Set base price based on pair
        base_prices = {
            "EUR_USD": Decimal('1.1000'),
            "GBP_USD": Decimal('1.2500'),
            "USD_JPY": Decimal('110.00')
        }
        base_price = base_prices.get(pair, Decimal('1.1000'))
        
        # Generate candles
        while current_time <= end_date:
            # Simulate realistic price movement
            volatility = Decimal('0.002')  # 0.2% volatility
            
            # Random price change
            price_change = Decimal(str(random.uniform(-float(volatility), float(volatility))))
            base_price += price_change
            
            # Ensure price stays positive
            if base_price <= 0:
                base_price = Decimal('0.001')
            
            # Create OHLC
            open_price = base_price
            high = base_price + Decimal(str(random.uniform(0, float(volatility * 2))))
            low = base_price - Decimal(str(random.uniform(0, float(volatility * 2))))
            close_price = base_price + Decimal(str(random.uniform(-float(volatility), float(volatility))))
            
            # Ensure OHLC relationship
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            candle = CandleData(
                timestamp=current_time,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=Decimal('1000')
            )
            candles.append(candle)
            
            # Move to next timeframe
            if timeframe == TimeFrame.M5:
                current_time += timedelta(minutes=5)
            elif timeframe == TimeFrame.M15:
                current_time += timedelta(minutes=15)
            elif timeframe == TimeFrame.H1:
                current_time += timedelta(hours=1)
        
        return candles
    
    def _print_basic_results(self, result: DebugBacktestResult):
        """Print basic backtest results."""
        print(f"\n📊 BASIC RESULTS:")
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Total Return: {result.total_return:+.2f}%")
        print(f"Profit Factor: {result.profit_factor:.3f}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        
        # Debug metrics
        print(f"\n🔍 DEBUG METRICS:")
        print(f"Total Signals: {result.total_signals_generated}")
        print(f"Signals Acted Upon: {result.signals_acted_upon}")
        print(f"Risk Checks Passed: {result.risk_checks_passed}")
        print(f"Risk Checks Failed: {result.risk_checks_failed}")


async def main():
    """Main function to run all examples."""
    
    print("🚀 Debug Backtesting System Examples")
    print("=" * 60)
    
    example = DebugBacktestingExample()
    
    try:
        # Example 1: Basic usage
        await example.example_basic_usage()
        
        # Example 2: Parameter optimization
        await example.example_parameter_optimization()
        
        # Example 3: Performance analysis
        await example.example_performance_analysis()
        
        print("\n🎉 All examples completed successfully!")
        print("📁 Check the 'example_reports' directory for detailed reports")
        
    except KeyboardInterrupt:
        print("\n🛑 Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
