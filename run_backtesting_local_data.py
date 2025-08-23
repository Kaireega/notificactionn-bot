#!/usr/bin/env python3
"""
Comprehensive Backtesting and Optimization Script
Demonstrates the complete backtesting and optimization capabilities of the trading bot.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
import json

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.backtest_engine import BacktestEngine, BacktestResult
from trading_bot.src.backtesting.optimizer import ParameterOptimizer, OptimizationResult
from trading_bot.src.backtesting.performance_metrics import PerformanceMetrics
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from api.oanda_api import OandaApi


class BacktestingDemo:
    """Demonstrates comprehensive backtesting and optimization capabilities."""
    
    def __init__(self):
        self.config = Config()
        self.oanda_api = OandaApi()
        self.performance_metrics = PerformanceMetrics()
        
    async def run_complete_demo(self):
        """Run the complete backtesting and optimization demo."""
        print("🚀 Starting Comprehensive Backtesting and Optimization Demo")
        print("=" * 70)
        
        # 1. Load historical data
        print("\n📊 Step 1: Loading Historical Data")
        historical_data = await self._load_historical_data()
        
        if not historical_data:
            print("❌ Failed to load historical data. Exiting.")
            return
        
        # 2. Run basic backtest
        print("\n🔍 Step 2: Running Basic Backtest")
        basic_result = await self._run_basic_backtest(historical_data)
        
        # 3. Run parameter optimization
        print("\n⚙️ Step 3: Running Parameter Optimization")
        optimization_result = await self._run_parameter_optimization(historical_data)
        
        # 4. Generate comprehensive reports
        print("\n📈 Step 4: Generating Reports")
        await self._generate_reports(basic_result, optimization_result)
        
        print("\n✅ Backtesting and Optimization Demo Completed!")
    
    async def _load_historical_data(self) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Load historical data for backtesting."""
        
        print("   Loading historical data for EUR_USD, GBP_USD, USD_JPY...")
        
        # Define date range (last 6 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        historical_data = {}
        pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]
        timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
        
        for pair in pairs:
            historical_data[pair] = {}
            
            for timeframe in timeframes:
                try:
                    # Fetch historical candles
                    candles_data = self.oanda_api.fetch_candles(
                        pair_name=pair,
                        count=1000,  # Get maximum data
                        granularity=timeframe.value,
                        date_f=start_date,
                        date_t=end_date
                    )
                    
                    if candles_data and 'candles' in candles_data:
                        # Convert to CandleData objects
                        candles = []
                        for candle_data in candles_data['candles']:
                            candle = CandleData(
                                timestamp=datetime.fromisoformat(candle_data['time'].replace('Z', '+00:00')),
                                open=Decimal(str(candle_data['mid']['o'])),
                                high=Decimal(str(candle_data['mid']['h'])),
                                low=Decimal(str(candle_data['mid']['l'])),
                                close=Decimal(str(candle_data['mid']['c'])),
                                volume=Decimal('1000')  # Default volume
                            )
                            candles.append(candle)
                        
                        historical_data[pair][timeframe] = candles
                        print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value}")
                        
                except Exception as e:
                    print(f"   ❌ Error loading data for {pair} {timeframe.value}: {e}")
                    # Create mock data for demonstration
                    historical_data[pair][timeframe] = self._create_mock_data(start_date, end_date, timeframe)
        
        return historical_data
    
    def _create_mock_data(self, start_date: datetime, end_date: datetime, timeframe: TimeFrame) -> List[CandleData]:
        """Create mock historical data for demonstration."""
        
        candles = []
        current_time = start_date
        base_price = Decimal('1.1000')
        
        # Generate mock data
        while current_time <= end_date:
            # Simulate price movement
            price_change = Decimal(str(random.uniform(-0.001, 0.001)))
            base_price += price_change
            
            high = base_price + Decimal('0.0005')
            low = base_price - Decimal('0.0005')
            open_price = base_price
            close_price = base_price + Decimal(str(random.uniform(-0.0002, 0.0002)))
            
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
    
    async def _run_basic_backtest(self, historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]]) -> BacktestResult:
        """Run a basic backtest with default parameters."""
        
        print("   Running backtest with default parameters...")
        
        # Define backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Last 3 months
        
        # Create backtest engine
        backtest_engine = BacktestEngine(self.config)
        
        # Run backtest
        result = await backtest_engine.run_backtest(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameters=None  # Use default parameters
        )
        
        # Print results
        print(f"   📊 Basic Backtest Results:")
        print(f"      Total Trades: {result.total_trades}")
        print(f"      Win Rate: {result.win_rate:.2%}")
        print(f"      Total Return: {result.total_return:.2%}")
        print(f"      Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"      Max Drawdown: {result.max_drawdown:.2%}")
        print(f"      Profit Factor: {result.profit_factor:.3f}")
        
        return result
    
    async def _run_parameter_optimization(self, historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]]) -> OptimizationResult:
        """Run parameter optimization."""
        
        print("   Running parameter optimization...")
        
        # Define parameter ranges to optimize
        parameter_ranges = {
            'rsi_oversold': [20, 25, 30, 35],
            'rsi_overbought': [65, 70, 75, 80],
            'macd_signal_threshold': [0.00005, 0.0001, 0.00015, 0.0002],
            'bollinger_threshold': [0.05, 0.1, 0.15, 0.2],
            'atr_multiplier': [1.5, 2.0, 2.5, 3.0],
            'min_signal_strength': [0.4, 0.5, 0.6, 0.7],
            'risk_percentage': [0.5, 1.0, 1.5, 2.0]
        }
        
        # Define backtest period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Last 2 months for optimization
        
        # Create optimizer
        optimizer = ParameterOptimizer(self.config)
        
        # Run optimization (using random search for speed)
        result = await optimizer.optimize_parameters(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameter_ranges=parameter_ranges,
            optimization_target='sharpe_ratio',
            method='random_search',
            max_iterations=50,  # Reduced for demo
            parallel=False
        )
        
        # Print results
        print(f"   🎯 Optimization Results:")
        print(f"      Method: {result.optimization_method}")
        print(f"      Iterations: {result.iterations}")
        print(f"      Best Score: {result.best_score:.4f}")
        print(f"      Best Parameters: {result.best_parameters}")
        print(f"      Execution Time: {result.execution_time:.2f} seconds")
        
        return result
    
    async def _generate_reports(self, basic_result: BacktestResult, optimization_result: OptimizationResult):
        """Generate comprehensive reports."""
        
        print("   Generating comprehensive reports...")
        
        # Generate performance report for basic backtest
        basic_report = self.performance_metrics.generate_performance_report(basic_result)
        
        # Generate optimization report
        optimizer = ParameterOptimizer(self.config)
        optimization_report = optimizer.generate_optimization_report(optimization_result)
        
        # Save reports to files
        self._save_report('basic_backtest_report.json', basic_report)
        self._save_report('optimization_report.json', optimization_report)
        
        # Print summary
        print(f"   📄 Reports saved:")
        print(f"      - basic_backtest_report.json")
        print(f"      - optimization_report.json")
        
        # Print comparison
        print(f"   📊 Performance Comparison:")
        print(f"      Basic Backtest:")
        print(f"         Sharpe Ratio: {basic_result.sharpe_ratio:.3f}")
        print(f"         Total Return: {basic_result.total_return:.2%}")
        print(f"         Max Drawdown: {basic_result.max_drawdown:.2%}")
        
        print(f"      Optimized Strategy:")
        print(f"         Sharpe Ratio: {optimization_result.best_result.sharpe_ratio:.3f}")
        print(f"         Total Return: {optimization_result.best_result.total_return:.2%}")
        print(f"         Max Drawdown: {optimization_result.best_result.max_drawdown:.2%}")
        
        # Calculate improvement
        sharpe_improvement = ((optimization_result.best_result.sharpe_ratio - basic_result.sharpe_ratio) / 
                             max(abs(basic_result.sharpe_ratio), 0.001)) * 100
        return_improvement = ((optimization_result.best_result.total_return - basic_result.total_return) / 
                             max(abs(basic_result.total_return), 0.001)) * 100
        
        print(f"   🚀 Improvements:")
        print(f"      Sharpe Ratio: {sharpe_improvement:+.1f}%")
        print(f"      Total Return: {return_improvement:+.1f}%")
    
    def _save_report(self, filename: str, data: Dict[str, Any]):
        """Save report to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"   ❌ Error saving report {filename}: {e}")


async def main():
    """Main function to run the backtesting demo."""
    
    print("🔧 Initializing Backtesting Demo...")
    
    try:
        demo = BacktestingDemo()
        await demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import random
    asyncio.run(main())
