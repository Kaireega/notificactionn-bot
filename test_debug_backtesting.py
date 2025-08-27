#!/usr/bin/env python3
"""
Test script for the debug backtesting system.
This script tests various aspects of the debug backtesting functionality.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from trading_bot.src.backtesting.debug_backtest_engine import DebugBacktestEngine
from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import CandleData, TimeFrame


class DebugBacktestingTester:
    """Test suite for debug backtesting functionality."""
    
    def __init__(self):
        self.config = Config()
        self.test_results = []
        
    def _create_mock_historical_data(self) -> dict:
        """Create mock historical data for testing."""
        print("   Creating mock historical data...")
        
        # Create more volatile data that should generate signals
        data = {}
        pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY']
        timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
        
        for pair in pairs:
            data[pair] = {}
            for timeframe in timeframes:
                candles = self._generate_mock_candles(pair, timeframe)
                data[pair][timeframe] = candles
                print(f"   ✅ Generated {len(candles)} candles for {pair} {timeframe.value}")
        
        return data
    
    def _generate_mock_candles(self, pair: str, timeframe: TimeFrame) -> list:
        """Generate mock candle data with more volatile patterns to trigger signals."""
        candles = []
        
        # Create more volatile data with clear trends and reversals
        base_price = 1.1000 if 'USD' in pair else 110.0
        current_price = base_price
        
        # Create data for last 30 days
        end_date = datetime.now().replace(tzinfo=timezone.utc)
        start_date = end_date - timedelta(days=30)
        
        # Calculate interval based on timeframe
        if timeframe == TimeFrame.M5:
            interval = timedelta(minutes=5)
            total_candles = 30 * 24 * 12  # 30 days * 24 hours * 12 (5-min intervals)
        elif timeframe == TimeFrame.M15:
            interval = timedelta(minutes=15)
            total_candles = 30 * 24 * 4   # 30 days * 24 hours * 4 (15-min intervals)
        else:  # H1
            interval = timedelta(hours=1)
            total_candles = 30 * 24       # 30 days * 24 hours
        
        # Create volatile price movements
        for i in range(total_candles):
            current_time = start_date + (interval * i)
            
            # Create more volatile price movements
            if i % 100 == 0:  # Every 100 candles, create a trend reversal
                trend_direction = 1 if (i // 100) % 2 == 0 else -1
                volatility = 0.005  # 50 pips volatility
            else:
                volatility = 0.001  # 10 pips normal volatility
            
            # Generate price movement
            price_change = (trend_direction * volatility * base_price) + (volatility * base_price * (i % 10 - 5) / 10)
            current_price += price_change
            
            # Ensure price stays reasonable
            if 'USD' in pair:
                current_price = max(0.8000, min(1.5000, current_price))
            else:
                current_price = max(80.0, min(150.0, current_price))
            
            # Create OHLC with more realistic spreads
            spread = 0.0001 if 'USD' in pair else 0.01
            open_price = current_price
            high = current_price + (volatility * base_price * 0.3)
            low = current_price - (volatility * base_price * 0.3)
            close_price = current_price + (price_change * 0.8)  # Close near the trend
            
            # Create RSI conditions (oversold/overbought)
            if i % 50 == 0:  # Every 50 candles, create RSI extremes
                if (i // 50) % 2 == 0:
                    # Oversold condition
                    close_price = low + (volatility * base_price * 0.1)
                else:
                    # Overbought condition
                    close_price = high - (volatility * base_price * 0.1)
            
            candle = CandleData(
                timestamp=current_time.replace(tzinfo=timezone.utc),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=Decimal('1000')
            )
            candles.append(candle)
        
        return candles
    
    async def test_basic_debug_backtest(self):
        """Test basic debug backtesting functionality."""
        print("🧪 Testing Basic Debug Backtesting")
        print("=" * 50)
        
        # Create mock data
        historical_data = self._create_mock_historical_data()
        
        # Define test parameters with more lenient settings
        start_date = datetime.now().replace(tzinfo=timezone.utc) - timedelta(days=30)
        end_date = datetime.now().replace(tzinfo=timezone.utc)
        
        # Use more lenient parameters that should generate trades
        parameters = {
            'rsi_oversold': 35,  # More lenient (was 30)
            'rsi_overbought': 65,  # More lenient (was 70)
            'risk_percentage': 1.0,
            'confidence_threshold': 0.3,  # Much more lenient (was 0.6)
            'signal_strength_threshold': 0.01,  # More lenient (was 0.04)
            'macd_signal_threshold': 0.00005  # More lenient (was 0.0001)
        }
        
        print("Test Parameters:")
        print(f"  Start Date: {start_date}")
        print(f"  End Date: {end_date}")
        print(f"  Parameters: {parameters}")
        
        # Create debug engine with lenient settings
        debug_engine = DebugBacktestEngine(self.config, debug_level='DETAILED')
        
        # Override config settings for testing
        debug_engine.config.technical_analysis.confidence_threshold = parameters['confidence_threshold']
        debug_engine.config.technical_analysis.signal_strength_threshold = parameters['signal_strength_threshold']
        debug_engine.config.technical_analysis.rsi_oversold = parameters['rsi_oversold']
        debug_engine.config.technical_analysis.rsi_overbought = parameters['rsi_overbought']
        
        # Run backtest
        result = await debug_engine.run_backtest(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        
        print("\n✅ Debug backtest completed successfully!")
        
        # Print results
        self._print_test_results(result)
        
        # Save debug report
        report_file = debug_engine.generate_debug_report(result, "test_debug_reports")
        print(f"\n📄 Debug report saved to: {report_file}")
        
        return result
    
    def _print_test_results(self, result):
        """Print formatted test results."""
        print("\n📊 TEST RESULTS SUMMARY")
        print("-" * 30)
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Total Return: {result.total_return:+.2f}%")
        print(f"Profit Factor: {result.profit_factor:.3f}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        
        print(f"\n🔍 DEBUG METRICS:")
        print(f"Total Signals: {result.total_signals_generated}")
        print(f"Signals Acted Upon: {result.signals_acted_upon}")
        print(f"Signals Ignored: {result.signals_ignored}")
        print(f"Risk Checks Passed: {result.risk_checks_passed}")
        print(f"Risk Checks Failed: {result.risk_checks_failed}")
        
        print(f"\n⏱️ PERFORMANCE TIMING:")
        print(f"Technical Analysis: {result.technical_analysis_time:.3f}s")
        print(f"Decision Making: {result.decision_making_time:.3f}s")
        print(f"Execution: {result.execution_time:.3f}s")
        
        print(f"\n🐛 DEBUG INFORMATION:")
        print(f"Debug Logs: {result.debug_logs}")
        print(f"Error Logs: {result.error_logs}")
        print(f"Warnings: {result.warnings}")
    
    async def test_performance_analysis(self):
        """Test performance analysis functionality."""
        print("\n🧪 Testing Performance Analysis")
        print("=" * 50)
        
        # Run basic test first
        result = await self.test_basic_debug_backtest()
        
        print("\n📈 PERFORMANCE ANALYSIS:")
        print(f"Total Return: {result.total_return:+.2f}%")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Profit Factor: {result.profit_factor:.3f}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        
        return result
    
    async def test_risk_analysis(self):
        """Test risk analysis functionality."""
        print("\n🧪 Testing Risk Analysis")
        print("=" * 50)
        
        # Run basic test first
        result = await self.test_basic_debug_backtest()
        
        print("\n⚠️ RISK ANALYSIS:")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        if result.max_drawdown < 5.0:
            print("  ✅ Low drawdown risk")
        elif result.max_drawdown < 10.0:
            print("  ⚠️ Moderate drawdown risk")
        else:
            print("  ❌ High drawdown risk")
        
        print(f"Max Consecutive Losses: {result.max_consecutive_losses}")
        if result.max_consecutive_losses < 3:
            print("  ✅ Low consecutive loss risk")
        elif result.max_consecutive_losses < 5:
            print("  ⚠️ Moderate consecutive loss risk")
        else:
            print("  ❌ High consecutive loss risk")
        
        return result
    
    async def test_signal_analysis(self):
        """Test signal analysis functionality."""
        print("\n🧪 Testing Signal Analysis")
        print("=" * 50)
        
        # Run basic test first
        result = await self.test_basic_debug_backtest()
        
        print("\n📡 SIGNAL ANALYSIS:")
        print(f"Total Signals Generated: {result.total_signals_generated}")
        print(f"Signals Acted Upon: {result.signals_acted_upon}")
        print(f"Signals Ignored: {result.signals_ignored}")
        
        if result.total_signals_generated > 0:
            signal_efficiency = (result.signals_acted_upon / result.total_signals_generated) * 100
            print(f"Signal Efficiency: {signal_efficiency:.1f}%")
        
        print(f"\n⏱️ TIMING ANALYSIS:")
        total_time = result.technical_analysis_time + result.decision_making_time + result.execution_time
        if total_time > 0:
            print(f"Total Processing Time: {total_time:.3f}s")
            print(f"Technical Analysis: {result.technical_analysis_time:.3f}s ({(result.technical_analysis_time/total_time)*100:.1f}%)")
            print(f"Decision Making: {result.decision_making_time:.3f}s ({(result.decision_making_time/total_time)*100:.1f}%)")
            print(f"Execution: {result.execution_time:.3f}s ({(result.execution_time/total_time)*100:.1f}%)")
        
        return result


async def main():
    """Main test function."""
    print("🚀 Starting Debug Backtesting Tests")
    print("=" * 60)
    
    # Initialize tester
    tester = DebugBacktestingTester()
    
    # Run all tests
    await tester.test_basic_debug_backtest()
    await tester.test_performance_analysis()
    await tester.test_risk_analysis()
    await tester.test_signal_analysis()
    
    print("\n🎉 All tests completed successfully!")
    print("📁 Check the 'test_debug_reports' directory for detailed reports")


if __name__ == "__main__":
    asyncio.run(main())
