#!/usr/bin/env python3
"""
Enhanced Debug Backtesting Runner
Provides comprehensive debugging and analysis capabilities for backtesting.
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import argparse
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
import pandas as pd
import numpy as np

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.backtesting.debug_backtest_engine import DebugBacktestEngine, DebugBacktestResult
from trading_bot.src.backtesting.optimizer import ParameterOptimizer, OptimizationResult
from trading_bot.src.backtesting.performance_metrics import PerformanceMetrics
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from api.oanda_api import OandaApi


class DebugBacktestingRunner:
    """Enhanced backtesting runner with comprehensive debugging capabilities."""
    
    def __init__(self, debug_level: str = "DETAILED"):
        self.config = Config()
        self.oanda_api = OandaApi()
        self.performance_metrics = PerformanceMetrics()
        self.debug_level = debug_level.upper()
        
        # Create output directories
        self.output_dir = Path("debug_output")
        self.output_dir.mkdir(exist_ok=True)
        
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "charts").mkdir(exist_ok=True)
        (self.output_dir / "data").mkdir(exist_ok=True)
        
    async def run_comprehensive_debug_backtest(
        self,
        pairs: List[str] = None,
        timeframes: List[TimeFrame] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        parameters: Dict[str, Any] = None,
        save_reports: bool = True,
        generate_charts: bool = True
    ) -> DebugBacktestResult:
        """Run a comprehensive debug backtest with extensive analysis."""
        
        print("🚀 Starting Comprehensive Debug Backtest")
        print("=" * 70)
        print(f"Debug Level: {self.debug_level}")
        print(f"Output Directory: {self.output_dir}")
        
        # Set default values
        if pairs is None:
            pairs = ["EUR_USD", "GBP_USD", "USD_JPY"]
        if timeframes is None:
            timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
        if end_date is None:
            end_date = datetime.now()
        
        print(f"Pairs: {pairs}")
        print(f"Timeframes: {[tf.value for tf in timeframes]}")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Parameters: {parameters}")
        
        # 1. Load and validate historical data
        print("\n📊 Step 1: Loading and Validating Historical Data")
        historical_data = await self._load_and_validate_historical_data(
            pairs, timeframes, start_date, end_date
        )
        
        if not historical_data:
            print("❌ Failed to load historical data. Exiting.")
            return None
        
        # 2. Run debug backtest
        print("\n🔍 Step 2: Running Debug Backtest")
        debug_result = await self._run_debug_backtest(
            historical_data, start_date, end_date, parameters
        )
        
        if not debug_result:
            print("❌ Debug backtest failed. Exiting.")
            return None
        
        # 3. Generate comprehensive analysis
        print("\n📈 Step 3: Generating Comprehensive Analysis")
        await self._generate_comprehensive_analysis(debug_result, save_reports, generate_charts)
        
        # 4. Print summary
        print("\n📋 Step 4: Summary Report")
        self._print_summary_report(debug_result)
        
        print("\n✅ Comprehensive Debug Backtest Completed!")
        return debug_result
    
    async def _load_and_validate_historical_data(
        self,
        pairs: List[str],
        timeframes: List[TimeFrame],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Load and validate historical data with debugging."""
        
        print("   Loading historical data...")
        
        historical_data = {}
        data_quality_report = {
            'total_pairs': len(pairs),
            'total_timeframes': len(timeframes),
            'data_points': {},
            'quality_issues': [],
            'missing_data': []
        }
        
        for pair in pairs:
            historical_data[pair] = {}
            
            for timeframe in timeframes:
                try:
                    # Fetch historical candles
                    candles_data = self.oanda_api.fetch_candles(
                        pair_name=pair,
                        count=1000,
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
                                volume=Decimal('1000')
                            )
                            candles.append(candle)
                        
                        # Validate data quality
                        quality_issues = self._validate_candle_data(candles, pair, timeframe)
                        if quality_issues:
                            data_quality_report['quality_issues'].extend(quality_issues)
                        
                        historical_data[pair][timeframe] = candles
                        data_quality_report['data_points'][f"{pair}_{timeframe.value}"] = len(candles)
                        
                        print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value}")
                        
                        # Check for sufficient data
                        if len(candles) < 100:
                            data_quality_report['missing_data'].append({
                                'pair': pair,
                                'timeframe': timeframe.value,
                                'candles': len(candles),
                                'min_required': 100
                            })
                        
                except Exception as e:
                    print(f"   ❌ Error loading data for {pair} {timeframe.value}: {e}")
                    data_quality_report['missing_data'].append({
                        'pair': pair,
                        'timeframe': timeframe.value,
                        'error': str(e)
                    })
                    # Create mock data for demonstration
                    historical_data[pair][timeframe] = self._create_mock_data(start_date, end_date, timeframe)
        
        # Save data quality report
        quality_report_file = self.output_dir / "data" / "data_quality_report.json"
        with open(quality_report_file, 'w') as f:
            json.dump(data_quality_report, f, indent=2, default=str)
        
        print(f"   📄 Data quality report saved to {quality_report_file}")
        
        return historical_data
    
    def _validate_candle_data(self, candles: List[CandleData], pair: str, timeframe: TimeFrame) -> List[Dict[str, Any]]:
        """Validate candle data quality."""
        issues = []
        
        if not candles:
            issues.append({
                'pair': pair,
                'timeframe': timeframe.value,
                'issue': 'No candles found',
                'severity': 'HIGH'
            })
            return issues
        
        # Check for gaps in data
        expected_interval = self._get_timeframe_interval(timeframe)
        for i in range(1, len(candles)):
            time_diff = candles[i].timestamp - candles[i-1].timestamp
            if time_diff > expected_interval * 2:
                issues.append({
                    'pair': pair,
                    'timeframe': timeframe.value,
                    'issue': f'Data gap detected: {time_diff} between candles {i-1} and {i}',
                    'severity': 'MEDIUM'
                })
        
        # Check for price anomalies
        for i, candle in enumerate(candles):
            if candle.high < candle.low:
                issues.append({
                    'pair': pair,
                    'timeframe': timeframe.value,
                    'issue': f'Invalid OHLC: high < low at candle {i}',
                    'severity': 'HIGH'
                })
            
            if candle.open < 0 or candle.high < 0 or candle.low < 0 or candle.close < 0:
                issues.append({
                    'pair': pair,
                    'timeframe': timeframe.value,
                    'issue': f'Negative price detected at candle {i}',
                    'severity': 'HIGH'
                })
        
        return issues
    
    def _get_timeframe_interval(self, timeframe: TimeFrame) -> timedelta:
        """Get expected time interval for timeframe."""
        if timeframe == TimeFrame.M5:
            return timedelta(minutes=5)
        elif timeframe == TimeFrame.M15:
            return timedelta(minutes=15)
        elif timeframe == TimeFrame.H1:
            return timedelta(hours=1)
        elif timeframe == TimeFrame.H4:
            return timedelta(hours=4)
        else:
            return timedelta(minutes=5)  # Default
    
    def _create_mock_data(self, start_date: datetime, end_date: datetime, timeframe: TimeFrame) -> List[CandleData]:
        """Create mock historical data for demonstration."""
        import random
        
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
    
    async def _run_debug_backtest(
        self,
        historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]],
        start_date: datetime,
        end_date: datetime,
        parameters: Optional[Dict[str, Any]] = None
    ) -> DebugBacktestResult:
        """Run debug backtest with comprehensive logging."""
        
        print("   Running debug backtest...")
        
        # Create debug backtest engine
        debug_engine = DebugBacktestEngine(self.config, debug_level=self.debug_level)
        
        # Run backtest
        start_time = time.time()
        result = await debug_engine.run_backtest(
            historical_data=historical_data,
            start_date=start_date,
            end_date=end_date,
            parameters=parameters
        )
        execution_time = time.time() - start_time
        
        print(f"   ✅ Debug backtest completed in {execution_time:.2f}s")
        print(f"   📊 Results: {result.total_trades} trades, {result.win_rate:.2%} win rate, {result.total_return:.2%} return")
        
        return result
    
    async def _generate_comprehensive_analysis(
        self,
        result: DebugBacktestResult,
        save_reports: bool = True,
        generate_charts: bool = True
    ):
        """Generate comprehensive analysis and reports."""
        
        print("   Generating analysis...")
        
        # Generate debug report
        if save_reports:
            # Create a debug engine to generate the report
            debug_engine = DebugBacktestEngine(self.config, debug_level=self.debug_level)
            report_file = debug_engine.generate_debug_report(result, str(self.output_dir / "reports"))
            print(f"   📄 Debug report saved to {report_file}")
        
        # Generate performance analysis
        performance_analysis = self._analyze_performance(result)
        
        # Generate risk analysis
        risk_analysis = self._analyze_risk(result)
        
        # Generate signal analysis
        signal_analysis = self._analyze_signals(result)
        
        # Save analysis reports
        if save_reports:
            analysis_file = self.output_dir / "reports" / "comprehensive_analysis.json"
            analysis_data = {
                'performance_analysis': performance_analysis,
                'risk_analysis': risk_analysis,
                'signal_analysis': signal_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            
            print(f"   📄 Comprehensive analysis saved to {analysis_file}")
        
        # Generate charts
        if generate_charts:
            await self._generate_charts(result)
    
    def _analyze_performance(self, result: DebugBacktestResult) -> Dict[str, Any]:
        """Analyze performance metrics."""
        analysis = {
            'overall_performance': {
                'total_return': result.total_return,
                'win_rate': result.win_rate,
                'profit_factor': result.profit_factor,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'avg_trade_duration': result.avg_trade_duration
            },
            'trade_analysis': {
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'avg_win': result.avg_win,
                'avg_loss': result.avg_loss,
                'largest_win': result.largest_win,
                'largest_loss': result.largest_loss
            },
            'performance_by_pair': result.performance_by_pair,
            'performance_by_signal_type': result.performance_by_signal_type,
            'consecutive_analysis': {
                'max_consecutive_wins': result.consecutive_wins,
                'max_consecutive_losses': result.consecutive_losses
            }
        }
        
        # Calculate additional metrics
        if result.total_trades > 0:
            analysis['additional_metrics'] = {
                'risk_reward_ratio': abs(result.avg_win / max(result.avg_loss, 0.01)),
                'expectancy': (result.win_rate / 100 * result.avg_win) - ((1 - result.win_rate / 100) * abs(result.avg_loss)),
                'kelly_criterion': (result.win_rate / 100 * result.avg_win - (1 - result.win_rate / 100) * abs(result.avg_loss)) / result.avg_win if result.avg_win > 0 else 0
            }
        
        return analysis
    
    def _analyze_risk(self, result: DebugBacktestResult) -> Dict[str, Any]:
        """Analyze risk metrics."""
        analysis = {
            'drawdown_analysis': {
                'max_drawdown': result.max_drawdown,
                'drawdown_severity': 'High' if result.max_drawdown > 20 else 'Medium' if result.max_drawdown > 10 else 'Low',
                'recovery_factor': result.total_return / max(result.max_drawdown, 0.01)
            },
            'risk_metrics': {
                'var_95': self._calculate_var(result, 0.95),
                'var_99': self._calculate_var(result, 0.99),
                'cvar_95': self._calculate_cvar(result, 0.95),
                'cvar_99': self._calculate_cvar(result, 0.99)
            },
            'consecutive_losses_risk': {
                'max_consecutive_losses': result.consecutive_losses,
                'risk_level': 'High' if result.consecutive_losses > 5 else 'Medium' if result.consecutive_losses > 3 else 'Low'
            },
            'risk_checks': {
                'passed': result.risk_checks_passed,
                'failed': result.risk_checks_failed,
                'pass_rate': result.risk_checks_passed / max(result.risk_checks_passed + result.risk_checks_failed, 1)
            }
        }
        
        return analysis
    
    def _analyze_signals(self, result: DebugBacktestResult) -> Dict[str, Any]:
        """Analyze signal generation and quality."""
        analysis = {
            'signal_generation': {
                'total_signals': result.total_signals_generated,
                'signals_acted_upon': result.signals_acted_upon,
                'signals_ignored': result.signals_ignored,
                'signal_efficiency': result.signals_acted_upon / max(result.total_signals_generated, 1)
            },
            'signal_quality': {
                'signal_to_trade_ratio': result.total_signals_generated / max(result.total_trades, 1),
                'avg_signals_per_day': result.total_signals_generated / max((result.end_date - result.start_date).days, 1)
            },
            'performance_timing': {
                'technical_analysis_time': result.technical_analysis_time,
                'decision_making_time': result.decision_making_time,
                'execution_time': result.execution_time,
                'total_processing_time': result.technical_analysis_time + result.decision_making_time + result.execution_time
            }
        }
        
        return analysis
    
    def _calculate_var(self, result: DebugBacktestResult, confidence_level: float) -> float:
        """Calculate Value at Risk."""
        if not result.trade_history:
            return 0.0
        
        returns = [trade.pnl for trade in result.trade_history if trade.pnl is not None]
        if not returns:
            return 0.0
        
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def _calculate_cvar(self, result: DebugBacktestResult, confidence_level: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)."""
        if not result.trade_history:
            return 0.0
        
        returns = [trade.pnl for trade in result.trade_history if trade.pnl is not None]
        if not returns:
            return 0.0
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return np.mean([r for r in returns if r <= var])
    
    async def _generate_charts(self, result: DebugBacktestResult):
        """Generate comprehensive charts and visualizations."""
        
        print("   Generating charts...")
        
        # Set style
        try:
            import seaborn as sns
            plt.style.use('seaborn-v0_8')
        except ImportError:
            plt.style.use('default')
        
        # 1. Equity Curve
        self._plot_equity_curve(result)
        
        # 2. Drawdown Chart
        self._plot_drawdown(result)
        
        # 3. Trade Distribution
        self._plot_trade_distribution(result)
        
        # 4. Performance by Pair
        self._plot_performance_by_pair(result)
        
        # 5. Signal Analysis
        self._plot_signal_analysis(result)
        
        # 6. Risk Analysis
        self._plot_risk_analysis(result)
        
        print(f"   📊 Charts saved to {self.output_dir / 'charts'}")
    
    def _plot_equity_curve(self, result: DebugBacktestResult):
        """Plot equity curve."""
        plt.figure(figsize=(12, 6))
        plt.plot(result.equity_curve, linewidth=2, color='blue', alpha=0.8)
        plt.title('Equity Curve', fontsize=14, fontweight='bold')
        plt.xlabel('Trade Number')
        plt.ylabel('Account Balance')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "charts" / "equity_curve.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_drawdown(self, result: DebugBacktestResult):
        """Plot drawdown chart."""
        equity_curve = np.array(result.equity_curve)
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max * 100
        
        plt.figure(figsize=(12, 6))
        plt.fill_between(range(len(drawdown)), drawdown, 0, color='red', alpha=0.3)
        plt.plot(drawdown, color='red', linewidth=1)
        plt.title('Drawdown Analysis', fontsize=14, fontweight='bold')
        plt.xlabel('Trade Number')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "charts" / "drawdown.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_trade_distribution(self, result: DebugBacktestResult):
        """Plot trade P&L distribution."""
        if not result.trade_history:
            plt.figure(figsize=(12, 6))
            plt.text(0.5, 0.5, 'No trades executed\nin this backtest', 
                    ha='center', va='center', fontsize=14, fontweight='bold')
            plt.title('Trade P&L Distribution', fontsize=14, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "trade_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
            return
        
        pnls = [trade.pnl for trade in result.trade_history if trade.pnl is not None]
        
        if not pnls:
            plt.figure(figsize=(12, 6))
            plt.text(0.5, 0.5, 'No P&L data available\nin this backtest', 
                    ha='center', va='center', fontsize=14, fontweight='bold')
            plt.title('Trade P&L Distribution', fontsize=14, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "trade_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()
            return
        
        plt.figure(figsize=(12, 6))
        plt.hist(pnls, bins=30, alpha=0.7, color='green', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Break-even')
        plt.title('Trade P&L Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('P&L')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "charts" / "trade_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_performance_by_pair(self, result: DebugBacktestResult):
        """Plot performance by currency pair."""
        if not result.performance_by_pair:
            return
        
        pairs = list(result.performance_by_pair.keys())
        win_rates = [result.performance_by_pair[pair]['win_rate'] for pair in pairs]
        total_pnls = [result.performance_by_pair[pair]['pnl'] for pair in pairs]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Win rates
        ax1.bar(pairs, win_rates, color='skyblue', alpha=0.7)
        ax1.set_title('Win Rate by Pair', fontweight='bold')
        ax1.set_ylabel('Win Rate (%)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Total P&L
        colors = ['green' if pnl > 0 else 'red' for pnl in total_pnls]
        ax2.bar(pairs, total_pnls, color=colors, alpha=0.7)
        ax2.set_title('Total P&L by Pair', fontweight='bold')
        ax2.set_ylabel('Total P&L')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "charts" / "performance_by_pair.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_signal_analysis(self, result: DebugBacktestResult):
        """Plot signal analysis."""
        signal_data = {
            'Generated': result.total_signals_generated,
            'Acted Upon': result.signals_acted_upon,
            'Ignored': result.signals_ignored
        }
        
        # Check if all values are zero
        if all(value == 0 for value in signal_data.values()):
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'No signals generated\nin this backtest', 
                    ha='center', va='center', fontsize=14, fontweight='bold')
            plt.title('Signal Analysis', fontsize=14, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "signal_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.figure(figsize=(10, 6))
            plt.pie(signal_data.values(), labels=signal_data.keys(), autopct='%1.1f%%', 
                    colors=['lightblue', 'lightgreen', 'lightcoral'])
            plt.title('Signal Analysis', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "signal_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def _plot_risk_analysis(self, result: DebugBacktestResult):
        """Plot risk analysis."""
        risk_data = {
            'Passed': result.risk_checks_passed,
            'Failed': result.risk_checks_failed
        }
        
        # Check if all values are zero
        if all(value == 0 for value in risk_data.values()):
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, 'No risk checks performed\nin this backtest', 
                    ha='center', va='center', fontsize=14, fontweight='bold')
            plt.title('Risk Check Analysis', fontsize=14, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "risk_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.figure(figsize=(10, 6))
            plt.pie(risk_data.values(), labels=risk_data.keys(), autopct='%1.1f%%',
                    colors=['lightgreen', 'lightcoral'])
            plt.title('Risk Check Analysis', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(self.output_dir / "charts" / "risk_analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
    
    def _print_summary_report(self, result: DebugBacktestResult):
        """Print comprehensive summary report."""
        
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE DEBUG BACKTEST SUMMARY")
        print("="*70)
        
        # Basic Performance
        print(f"\n🎯 BASIC PERFORMANCE:")
        print(f"   Total Return: {result.total_return:+.2f}%")
        print(f"   Win Rate: {result.win_rate:.2f}%")
        print(f"   Profit Factor: {result.profit_factor:.3f}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"   Max Drawdown: {result.max_drawdown:.2f}%")
        
        # Trade Statistics
        print(f"\n📈 TRADE STATISTICS:")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Winning Trades: {result.winning_trades}")
        print(f"   Losing Trades: {result.losing_trades}")
        print(f"   Average Win: ${result.avg_win:.2f}")
        print(f"   Average Loss: ${result.avg_loss:.2f}")
        print(f"   Largest Win: ${result.largest_win:.2f}")
        print(f"   Largest Loss: ${result.largest_loss:.2f}")
        
        # Signal Analysis
        print(f"\n📡 SIGNAL ANALYSIS:")
        print(f"   Total Signals Generated: {result.total_signals_generated}")
        print(f"   Signals Acted Upon: {result.signals_acted_upon}")
        print(f"   Signals Ignored: {result.signals_ignored}")
        print(f"   Signal Efficiency: {result.signals_acted_upon/max(result.total_signals_generated, 1)*100:.1f}%")
        
        # Risk Analysis
        print(f"\n⚠️ RISK ANALYSIS:")
        print(f"   Risk Checks Passed: {result.risk_checks_passed}")
        print(f"   Risk Checks Failed: {result.risk_checks_failed}")
        print(f"   Max Consecutive Losses: {result.consecutive_losses}")
        print(f"   Max Consecutive Wins: {result.consecutive_wins}")
        
        # Performance Timing
        print(f"\n⏱️ PERFORMANCE TIMING:")
        print(f"   Technical Analysis Time: {result.technical_analysis_time:.3f}s")
        print(f"   Decision Making Time: {result.decision_making_time:.3f}s")
        print(f"   Execution Time: {result.execution_time:.3f}s")
        
        # Performance by Categories
        if result.performance_by_pair:
            print(f"\n💱 PERFORMANCE BY PAIR:")
            for pair, data in result.performance_by_pair.items():
                print(f"   {pair}: {data['trades']} trades, {data['win_rate']:.1f}% win rate, ${data['pnl']:.2f} P&L")
        
        if result.performance_by_signal_type:
            print(f"\n📊 PERFORMANCE BY SIGNAL TYPE:")
            for signal, data in result.performance_by_signal_type.items():
                print(f"   {signal}: {data['trades']} trades, {data['win_rate']:.1f}% win rate, ${data['pnl']:.2f} P&L")
        
        # Debug Information
        print(f"\n🐛 DEBUG INFORMATION:")
        print(f"   Debug Logs: {len(result.debug_logs)}")
        print(f"   Error Logs: {len(result.error_logs)}")
        print(f"   Warnings: {len(result.warnings)}")
        
        if result.error_logs:
            print(f"\n❌ ERRORS DETECTED:")
            for error in result.error_logs[-5:]:  # Show last 5 errors
                print(f"   {error}")
        
        if result.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in result.warnings[-5:]:  # Show last 5 warnings
                print(f"   {warning}")
        
        print("\n" + "="*70)


async def main():
    """Main function to run the debug backtesting."""
    
    parser = argparse.ArgumentParser(description='Run comprehensive debug backtesting')
    parser.add_argument('--debug-level', choices=['BASIC', 'DETAILED', 'VERBOSE'], 
                       default='DETAILED', help='Debug level')
    parser.add_argument('--pairs', nargs='+', default=['EUR_USD', 'GBP_USD', 'USD_JPY'],
                       help='Currency pairs to test')
    parser.add_argument('--timeframes', nargs='+', default=['M5', 'M15', 'H1'],
                       help='Timeframes to test')
    parser.add_argument('--days', type=int, default=90, help='Number of days to backtest')
    parser.add_argument('--no-reports', action='store_true', help='Skip generating reports')
    parser.add_argument('--no-charts', action='store_true', help='Skip generating charts')
    
    args = parser.parse_args()
    
    # Convert timeframes to TimeFrame objects
    timeframe_map = {'M5': TimeFrame.M5, 'M15': TimeFrame.M15, 'H1': TimeFrame.H1, 'H4': TimeFrame.H4}
    timeframes = [timeframe_map[tf] for tf in args.timeframes if tf in timeframe_map]
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    print("🔧 Initializing Debug Backtesting...")
    
    try:
        runner = DebugBacktestingRunner(debug_level=args.debug_level)
        result = await runner.run_comprehensive_debug_backtest(
            pairs=args.pairs,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            save_reports=not args.no_reports,
            generate_charts=not args.no_charts
        )
        
        if result:
            print(f"\n🎉 Debug backtesting completed successfully!")
            print(f"📁 Check the output directory: {runner.output_dir}")
        else:
            print("\n❌ Debug backtesting failed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Debug backtesting interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running debug backtesting: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
