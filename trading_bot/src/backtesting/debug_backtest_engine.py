"""
Enhanced Backtesting Engine with Comprehensive Debugging
Provides extensive debugging capabilities for backtesting analysis.
"""
import asyncio
import traceback
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
from collections import defaultdict, deque

from ..core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame, TradeDecision
)
from ..utils.config import Config
from ..utils.logger import get_logger
from ..ai.technical_analysis_layer import TechnicalAnalysisLayer
from ..decision.technical_decision_layer import TechnicalDecisionLayer
from ..decision.risk_manager_improved import ImprovedRiskManager
from .performance_metrics import PerformanceMetrics
from .simulation_broker import SimulationBroker


@dataclass
class DebugTradeRecord:
    """Enhanced trade record with debugging information."""
    trade_id: str
    pair: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    pnl: Optional[float]
    return_pct: Optional[float]
    reason: str
    signal: str
    
    # Debug information
    technical_indicators: Dict[str, Any]
    market_context: Dict[str, Any]
    decision_factors: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    execution_details: Dict[str, Any]
    
    # Performance tracking
    drawdown_at_entry: float
    equity_at_entry: float
    equity_at_exit: Optional[float]
    consecutive_wins_at_entry: int
    consecutive_losses_at_entry: int


@dataclass
class DebugBacktestResult:
    """Enhanced backtest results with debugging information."""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_duration: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    
    # Debug metrics
    total_signals_generated: int
    signals_acted_upon: int
    signals_ignored: int
    risk_checks_passed: int
    risk_checks_failed: int
    technical_analysis_time: float
    decision_making_time: float
    execution_time: float
    
    # Detailed data
    equity_curve: List[float]
    trade_history: List[DebugTradeRecord]
    signal_history: List[Dict[str, Any]]
    risk_history: List[Dict[str, Any]]
    performance_by_pair: Dict[str, Dict[str, float]]
    performance_by_timeframe: Dict[str, Dict[str, float]]
    performance_by_signal_type: Dict[str, Dict[str, float]]
    
    # Configuration
    parameter_set: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    
    # Debug information
    debug_logs: List[str]
    error_logs: List[str]
    warnings: List[str]
    execution_summary: Dict[str, Any]


class DebugBacktestEngine:
    """Enhanced backtesting engine with comprehensive debugging capabilities."""
    
    def __init__(self, config: Config, debug_level: str = "DETAILED"):
        self.config = config
        self.debug_level = debug_level.upper()
        
        # Enhanced logging
        self.logger = self._setup_debug_logger()
        
        # Initialize components
        self.technical_layer = TechnicalAnalysisLayer(config)
        self.decision_layer = TechnicalDecisionLayer(config)
        self.risk_manager = ImprovedRiskManager(config)
        self.broker = SimulationBroker(config)
        self.performance_metrics = PerformanceMetrics()
        
        # Backtest state
        self.current_balance = config.simulation.initial_balance
        self.initial_balance = config.simulation.initial_balance
        self.equity_curve = []
        self.trade_history = []
        self.open_positions = {}
        
        # Debug state
        self.debug_logs = []
        self.error_logs = []
        self.warnings = []
        self.signal_history = []
        self.risk_history = []
        self.performance_timers = defaultdict(float)
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal('0.0')
        self.total_signals = 0
        self.signals_acted_upon = 0
        self.signals_ignored = 0
        self.risk_checks_passed = 0
        self.risk_checks_failed = 0
        
        # Trade ID counter
        self.trade_id_counter = 0
        
        # Performance by categories
        self.performance_by_pair = defaultdict(lambda: {
            'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'win_rate': 0.0
        })
        self.performance_by_timeframe = defaultdict(lambda: {
            'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'win_rate': 0.0
        })
        self.performance_by_signal_type = defaultdict(lambda: {
            'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'win_rate': 0.0
        })
        
    def _setup_debug_logger(self) -> logging.Logger:
        """Setup enhanced debug logger."""
        logger = logging.getLogger(f"{__name__}_debug")
        logger.setLevel(logging.DEBUG)
        
        # Create debug directory
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)
        
        # File handler for detailed logs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(debug_dir / f"backtest_debug_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _log_debug(self, message: str, level: str = "INFO"):
        """Log debug message with timestamp."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        
        if level == "ERROR":
            self.error_logs.append(log_entry)
        elif level == "WARNING":
            self.warnings.append(log_entry)
        else:
            self.debug_logs.append(log_entry)
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "DEBUG":
            self.logger.debug(message)
        else:
            self.logger.info(message)
    
    def _start_timer(self, timer_name: str):
        """Start a performance timer."""
        self.performance_timers[f"{timer_name}_start"] = time.time()
    
    def _end_timer(self, timer_name: str) -> float:
        """End a performance timer and return duration."""
        start_time = self.performance_timers.get(f"{timer_name}_start", time.time())
        duration = time.time() - start_time
        self.performance_timers[timer_name] = duration
        return duration
    
    async def run_backtest(
        self,
        historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]],
        start_date: datetime,
        end_date: datetime,
        parameters: Optional[Dict[str, Any]] = None
    ) -> DebugBacktestResult:
        """Run a complete backtest with extensive debugging."""
        
        self._log_debug(f"Starting enhanced backtest from {start_date} to {end_date}", "INFO")
        self._log_debug(f"Debug level: {self.debug_level}", "INFO")
        self._log_debug(f"Parameters: {parameters}", "DEBUG")
        
        # Reset state
        self._reset_backtest_state()
        
        # Apply custom parameters if provided
        if parameters:
            self._apply_parameters(parameters)
        
        # Ensure initial balance is Decimal
        self.current_balance = Decimal(str(self.current_balance))
        self.initial_balance = Decimal(str(self.initial_balance))
        
        # Sort all candles by timestamp
        self._start_timer("data_preparation")
        all_candles = self._prepare_historical_data(historical_data, start_date, end_date)
        data_prep_time = self._end_timer("data_preparation")
        self._log_debug(f"Data preparation completed in {data_prep_time:.3f}s", "INFO")
        
        # Process each candle
        total_candles = len(all_candles)
        processed_candles = 0
        
        for timestamp, candles_by_pair in all_candles.items():
            processed_candles += 1
            
            if processed_candles % 1000 == 0:
                progress = (processed_candles / total_candles) * 100
                self._log_debug(f"Progress: {progress:.1f}% ({processed_candles}/{total_candles})", "INFO")
            
            await self._process_timestamp_debug(timestamp, candles_by_pair)
            
            # Update equity curve
            self.equity_curve.append(float(self.current_balance))
        
        # Close all remaining open positions at the end of backtest
        if self.open_positions:
            self._log_debug(f"Closing {len(self.open_positions)} remaining open positions", "INFO")
            for pair, position in list(self.open_positions.items()):
                last_candles = all_candles[list(all_candles.keys())[-1]]
                if pair in last_candles:
                    current_price = self._get_current_price(last_candles[pair].get(TimeFrame.M5, []))
                    await self._close_position_debug(pair, 'end_of_backtest', current_price, list(all_candles.keys())[-1])
        
        # Calculate final results
        self._start_timer("results_calculation")
        result = self._calculate_debug_backtest_results(start_date, end_date, parameters or {})
        results_time = self._end_timer("results_calculation")
        
        self._log_debug(f"Results calculation completed in {results_time:.3f}s", "INFO")
        self._log_debug(f"Backtest completed: {result.total_trades} trades, "
                       f"Win rate: {result.win_rate:.2%}, "
                       f"Return: {result.total_return:.2%}", "INFO")
        
        return result
    
    def _reset_backtest_state(self):
        """Reset backtest state for a new run."""
        self.current_balance = self.initial_balance
        self.equity_curve = [float(self.initial_balance)]
        self.trade_history = []
        self.open_positions = {}
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal('0.0')
        self.total_signals = 0
        self.signals_acted_upon = 0
        self.signals_ignored = 0
        self.risk_checks_passed = 0
        self.risk_checks_failed = 0
        self.trade_id_counter = 0
        
        # Reset performance tracking
        self.performance_by_pair.clear()
        self.performance_by_timeframe.clear()
        self.performance_by_signal_type.clear()
        
        # Reset debug state
        self.debug_logs.clear()
        self.error_logs.clear()
        self.warnings.clear()
        self.signal_history.clear()
        self.risk_history.clear()
        self.performance_timers.clear()
        
        self._log_debug("Backtest state reset", "DEBUG")
    
    def _apply_parameters(self, parameters: Dict[str, Any]):
        """Apply custom parameters to the trading system."""
        self._log_debug(f"Applying parameters: {parameters}", "DEBUG")
        
        # Technical analysis parameters
        if 'rsi_oversold' in parameters:
            self.technical_layer.rsi_oversold = parameters['rsi_oversold']
        if 'rsi_overbought' in parameters:
            self.technical_layer.rsi_overbought = parameters['rsi_overbought']
        if 'macd_signal_threshold' in parameters:
            self.technical_layer.macd_signal_threshold = parameters['macd_signal_threshold']
        if 'bollinger_threshold' in parameters:
            self.technical_layer.bollinger_threshold = parameters['bollinger_threshold']
        if 'atr_multiplier' in parameters:
            self.technical_layer.atr_multiplier = parameters['atr_multiplier']
        if 'min_signal_strength' in parameters:
            self.technical_layer.min_signal_strength = parameters['min_signal_strength']
        
        # Risk management parameters
        if 'risk_percentage' in parameters:
            self.config.trading.risk_percentage = parameters['risk_percentage']
        if 'max_daily_loss' in parameters:
            self.config.risk_management.max_daily_loss = parameters['max_daily_loss']
        if 'max_open_trades' in parameters:
            self.config.risk_management.max_open_trades = parameters['max_open_trades']
    
    def _prepare_historical_data(
        self, 
        historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[datetime, Dict[str, Dict[TimeFrame, List[CandleData]]]]:
        """Prepare historical data sorted by timestamp with debugging."""
        
        self._log_debug("Starting historical data preparation", "DEBUG")
        
        # Flatten and sort all candles by timestamp
        all_candles = []
        total_candles = 0
        filtered_candles = 0
        
        for pair, timeframes in historical_data.items():
            for timeframe, candles in timeframes.items():
                total_candles += len(candles)
                for candle in candles:
                    # Ensure candle timestamp is timezone-aware
                    candle_timestamp = candle.timestamp
                    if candle_timestamp.tzinfo is None:
                        candle_timestamp = candle_timestamp.replace(tzinfo=timezone.utc)
                    
                    if start_date <= candle_timestamp <= end_date:
                        all_candles.append((candle_timestamp, pair, timeframe, candle))
                        filtered_candles += 1
        
        self._log_debug(f"Data preparation: {total_candles} total candles, {filtered_candles} within date range", "INFO")
        
        # Sort by timestamp
        all_candles.sort(key=lambda x: x[0])
        
        # Group by timestamp
        grouped_candles = {}
        for timestamp, pair, timeframe, candle in all_candles:
            if timestamp not in grouped_candles:
                grouped_candles[timestamp] = {}
            if pair not in grouped_candles[timestamp]:
                grouped_candles[timestamp][pair] = {}
            if timeframe not in grouped_candles[timestamp][pair]:
                grouped_candles[timestamp][pair][timeframe] = []
            grouped_candles[timestamp][pair][timeframe].append(candle)
        
        self._log_debug(f"Grouped into {len(grouped_candles)} unique timestamps", "DEBUG")
        return grouped_candles
    
    async def _process_timestamp_debug(self, timestamp: datetime, candles_by_pair: Dict[str, Dict[TimeFrame, List[CandleData]]]):
        """Process all candles for a specific timestamp with debugging."""
        
        for pair, timeframes in candles_by_pair.items():
            # Skip if we already have an open position for this pair
            if pair in self.open_positions:
                continue
            
            # Skip if we've reached max open trades
            if len(self.open_positions) >= self.config.risk_management.max_open_trades:
                continue
            
            try:
                # Get current price from M5 timeframe
                m5_candles = timeframes.get(TimeFrame.M5, [])
                if not m5_candles:
                    continue
                
                current_price = self._get_current_price(m5_candles)
                
                # Create market context
                market_context = self._create_market_context(timeframes)
                
                # Analyze technical indicators with timing
                self._start_timer("technical_analysis")
                technical_indicators = {}
                for tf, candles in timeframes.items():
                    if len(candles) >= 20:  # Minimum candles for indicators
                        indicators = self.technical_layer.technical_analyzer.calculate_indicators(candles)
                        technical_indicators[tf] = indicators
                tech_analysis_time = self._end_timer("technical_analysis")
                
                if not technical_indicators:
                    continue
                
                # Make trading decision with timing
                self._start_timer("decision_making")
                decision = await self.decision_layer.make_technical_decision(
                    pair, technical_indicators, market_context, current_price, timeframes
                )
                decision_time = self._end_timer("decision_making")
                
                # Record signal
                signal_record = {
                    'timestamp': timestamp,
                    'pair': pair,
                    'current_price': float(current_price),
                    'technical_indicators': technical_indicators,
                    'market_context': asdict(market_context),
                    'decision': decision.to_dict() if decision else None,
                    'tech_analysis_time': tech_analysis_time,
                    'decision_time': decision_time,
                    'open_positions': len(self.open_positions),
                    'current_balance': float(self.current_balance)
                }
                self.signal_history.append(signal_record)
                
                self.total_signals += 1
                
                if decision and decision.approved:
                    self.signals_acted_upon += 1
                    # Execute trade with timing
                    self._start_timer("trade_execution")
                    await self._execute_trade_debug(pair, decision, current_price, timestamp, 
                                                   technical_indicators, market_context)
                    execution_time = self._end_timer("trade_execution")
                    self._log_debug(f"Trade execution completed in {execution_time:.3f}s", "DEBUG")
                else:
                    self.signals_ignored += 1
                    if self.debug_level == "DETAILED":
                        self._log_debug(f"Signal ignored for {pair} at {timestamp}: {decision.reason if decision else 'No decision'}", "DEBUG")
                
            except Exception as e:
                self._log_debug(f"Error processing {pair} at {timestamp}: {e}", "ERROR")
                self._log_debug(traceback.format_exc(), "ERROR")
                continue
    
    def _create_market_context(self, timeframes: Dict[TimeFrame, List[CandleData]]) -> MarketContext:
        """Create market context from timeframe data."""
        # Enhanced market context calculation
        volatility = 0.002
        trend_strength = 0.5
        
        # Calculate volatility from recent candles
        if TimeFrame.M5 in timeframes and len(timeframes[TimeFrame.M5]) >= 20:
            recent_candles = timeframes[TimeFrame.M5][-20:]
            returns = []
            for i in range(1, len(recent_candles)):
                ret = (recent_candles[i].close - recent_candles[i-1].close) / recent_candles[i-1].close
                returns.append(float(ret))
            volatility = np.std(returns) if returns else 0.002
        
        return MarketContext(
            condition=MarketCondition.UNKNOWN,
            volatility=volatility,
            trend_strength=trend_strength
        )
    
    def _get_current_price(self, candles: List[CandleData]) -> Decimal:
        """Get current price from the latest candle."""
        if not candles:
            return Decimal('0')
        return candles[-1].close
    
    async def _execute_trade_debug(self, pair: str, decision: TradeDecision, current_price: Decimal, 
                                 timestamp: datetime, technical_indicators: Dict, market_context: MarketContext):
        """Execute a trade based on the decision with debugging."""
        try:
            # Generate trade ID
            self.trade_id_counter += 1
            trade_id = f"T{self.trade_id_counter:06d}"
            
            # Calculate position size
            risk_amount = self.current_balance * (self.config.trading.risk_percentage / 100)
            position_size = risk_amount / abs(float(current_price - decision.modified_stop_loss))
            
            # Risk check
            risk_check_result = self._perform_risk_check(pair, position_size, current_price)
            
            if not risk_check_result['passed']:
                self.risk_checks_failed += 1
                self._log_debug(f"Risk check failed for {pair}: {risk_check_result['reason']}", "WARNING")
                return
            
            self.risk_checks_passed += 1
            
            # Execute through broker
            trade_result = await self.broker.execute_trade(
                pair=pair,
                side=decision.recommendation.signal.value,
                size=position_size,
                price=current_price,
                stop_loss=decision.modified_stop_loss,
                take_profit=decision.modified_take_profit
            )
            
            if trade_result['success']:
                # Calculate current drawdown
                current_drawdown = self._calculate_current_drawdown()
                
                # Create debug trade record
                debug_record = DebugTradeRecord(
                    trade_id=trade_id,
                    pair=pair,
                    entry_time=timestamp,
                    exit_time=None,
                    entry_price=float(current_price),
                    exit_price=None,
                    position_size=float(position_size),
                    pnl=None,
                    return_pct=None,
                    reason="entry",
                    signal=decision.recommendation.signal.value,
                    technical_indicators=technical_indicators,
                    market_context=asdict(market_context),
                    decision_factors=decision.to_dict(),
                    risk_metrics=risk_check_result,
                    execution_details=trade_result,
                    drawdown_at_entry=current_drawdown,
                    equity_at_entry=float(self.current_balance),
                    equity_at_exit=None,
                    consecutive_wins_at_entry=self._get_consecutive_wins(),
                    consecutive_losses_at_entry=self._get_consecutive_losses()
                )
                
                self.open_positions[pair] = {
                    'decision': decision,
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'position_size': position_size,
                    'stop_loss': decision.modified_stop_loss,
                    'take_profit': decision.modified_take_profit,
                    'debug_record': debug_record
                }
                
                self._log_debug(f"Opened {decision.recommendation.signal.value} position for {pair} "
                               f"at {current_price}, size: {position_size:.2f}, ID: {trade_id}", "INFO")
            
        except Exception as e:
            self._log_debug(f"Error executing trade for {pair}: {e}", "ERROR")
            self._log_debug(traceback.format_exc(), "ERROR")
    
    def _perform_risk_check(self, pair: str, position_size: float, current_price: Decimal) -> Dict[str, Any]:
        """Perform comprehensive risk check."""
        result = {
            'passed': True,
            'reason': 'All checks passed',
            'checks': {}
        }
        
        # Check position size
        max_position_size = float(self.current_balance) * 0.1  # Max 10% of balance
        if position_size > max_position_size:
            result['passed'] = False
            result['reason'] = 'Position size too large'
            result['checks']['position_size'] = {
                'actual': position_size,
                'max_allowed': max_position_size,
                'passed': False
            }
        else:
            result['checks']['position_size'] = {
                'actual': position_size,
                'max_allowed': max_position_size,
                'passed': True
            }
        
        # Check daily loss limit
        daily_pnl = self._calculate_daily_pnl()
        max_daily_loss = float(self.current_balance) * (self.config.risk_management.max_daily_loss / 100)
        if daily_pnl < -max_daily_loss:
            result['passed'] = False
            result['reason'] = 'Daily loss limit exceeded'
            result['checks']['daily_loss'] = {
                'actual': daily_pnl,
                'max_allowed': -max_daily_loss,
                'passed': False
            }
        else:
            result['checks']['daily_loss'] = {
                'actual': daily_pnl,
                'max_allowed': -max_daily_loss,
                'passed': True
            }
        
        return result
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate P&L for the current day."""
        today = datetime.now().date()
        daily_pnl = 0.0
        
        for trade in self.trade_history:
            if trade.entry_time.date() == today:
                if trade.pnl is not None:
                    daily_pnl += trade.pnl
        
        return daily_pnl
    
    def _calculate_current_drawdown(self) -> float:
        """Calculate current drawdown."""
        if not self.equity_curve:
            return 0.0
        
        peak = max(self.equity_curve)
        current = self.equity_curve[-1]
        return ((peak - current) / peak) * 100 if peak > 0 else 0.0
    
    def _get_consecutive_wins(self) -> int:
        """Get current consecutive wins."""
        consecutive = 0
        for trade in reversed(self.trade_history):
            if trade.pnl and trade.pnl > 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    def _get_consecutive_losses(self) -> int:
        """Get current consecutive losses."""
        consecutive = 0
        for trade in reversed(self.trade_history):
            if trade.pnl and trade.pnl < 0:
                consecutive += 1
            else:
                break
        return consecutive
    
    async def _close_position_debug(self, pair: str, reason: str, current_price: Decimal, timestamp: datetime):
        """Close an open position with debugging."""
        if pair not in self.open_positions:
            return
        
        position = self.open_positions[pair]
        entry_price = position['entry_price']
        position_size = position['position_size']
        debug_record = position['debug_record']
        
        # Calculate P&L
        if position['decision'].recommendation.signal == TradeSignal.BUY:
            pnl = (current_price - entry_price) * position_size
        else:
            pnl = (entry_price - current_price) * position_size
        
        # Update balance
        self.current_balance += pnl
        self.total_pnl += pnl
        
        # Update trade statistics
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update debug record
        debug_record.exit_time = timestamp
        debug_record.exit_price = float(current_price)
        debug_record.pnl = float(pnl)
        debug_record.return_pct = float(pnl / (entry_price * position_size) * 100)
        debug_record.reason = reason
        debug_record.equity_at_exit = float(self.current_balance)
        
        # Update performance by categories
        self._update_performance_categories(pair, pnl, debug_record.signal)
        
        # Add to trade history
        self.trade_history.append(debug_record)
        
        # Remove from open positions
        del self.open_positions[pair]
        
        self._log_debug(f"Closed {pair} position: {pnl:.2f} P&L ({reason})", "INFO")
    
    def _update_performance_categories(self, pair: str, pnl: Decimal, signal: str):
        """Update performance tracking by categories."""
        # Update by pair
        self.performance_by_pair[pair]['trades'] += 1
        self.performance_by_pair[pair]['pnl'] += float(pnl)
        if pnl > 0:
            self.performance_by_pair[pair]['wins'] += 1
        else:
            self.performance_by_pair[pair]['losses'] += 1
        
        # Update by signal type
        self.performance_by_signal_type[signal]['trades'] += 1
        self.performance_by_signal_type[signal]['pnl'] += float(pnl)
        if pnl > 0:
            self.performance_by_signal_type[signal]['wins'] += 1
        else:
            self.performance_by_signal_type[signal]['losses'] += 1
    
    def _calculate_debug_backtest_results(self, start_date: datetime, end_date: datetime, parameters: Dict[str, Any]) -> DebugBacktestResult:
        """Calculate comprehensive backtest results with debugging information."""
        
        # Basic metrics
        total_return = float(self.current_balance - self.initial_balance) / float(self.initial_balance) * 100
        win_rate = self.winning_trades / max(self.total_trades, 1) * 100
        
        # Calculate profit factor
        total_wins = sum(t.pnl for t in self.trade_history if t.pnl and t.pnl > 0)
        total_losses = abs(sum(t.pnl for t in self.trade_history if t.pnl and t.pnl < 0))
        profit_factor = total_wins / max(total_losses, 0.01)
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Calculate Sharpe ratio (simplified)
        if len(self.trade_history) > 1:
            returns = [t.return_pct for t in self.trade_history if t.return_pct is not None]
            sharpe_ratio = np.mean(returns) / max(np.std(returns), 0.01) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Calculate average trade duration
        if self.trade_history:
            durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 
                        for t in self.trade_history if t.exit_time]
            avg_duration = np.mean(durations) if durations else 0.0
        else:
            avg_duration = 0.0
        
        # Calculate other metrics
        if self.trade_history:
            wins = [t.pnl for t in self.trade_history if t.pnl and t.pnl > 0]
            losses = [t.pnl for t in self.trade_history if t.pnl and t.pnl < 0]
            
            avg_win = np.mean(wins) if wins else 0.0
            avg_loss = np.mean(losses) if losses else 0.0
            largest_win = max(wins) if wins else 0.0
            largest_loss = min(losses) if losses else 0.0
        else:
            avg_win = avg_loss = largest_win = largest_loss = 0.0
        
        # Calculate consecutive wins/losses
        consecutive_wins = self._calculate_consecutive_wins()
        consecutive_losses = self._calculate_consecutive_losses()
        
        # Calculate win rates for categories
        for pair_data in self.performance_by_pair.values():
            pair_data['win_rate'] = (pair_data['wins'] / max(pair_data['trades'], 1)) * 100
        
        for signal_data in self.performance_by_signal_type.values():
            signal_data['win_rate'] = (signal_data['wins'] / max(signal_data['trades'], 1)) * 100
        
        # Create execution summary
        execution_summary = {
            'total_candles_processed': len(self.equity_curve),
            'total_signals_generated': self.total_signals,
            'signals_acted_upon': self.signals_acted_upon,
            'signals_ignored': self.signals_ignored,
            'risk_checks_passed': self.risk_checks_passed,
            'risk_checks_failed': self.risk_checks_failed,
            'performance_timers': dict(self.performance_timers),
            'memory_usage': self._get_memory_usage(),
            'execution_time': sum(self.performance_timers.values())
        }
        
        return DebugBacktestResult(
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration=avg_duration,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            total_signals_generated=self.total_signals,
            signals_acted_upon=self.signals_acted_upon,
            signals_ignored=self.signals_ignored,
            risk_checks_passed=self.risk_checks_passed,
            risk_checks_failed=self.risk_checks_failed,
            technical_analysis_time=self.performance_timers.get('technical_analysis', 0),
            decision_making_time=self.performance_timers.get('decision_making', 0),
            execution_time=self.performance_timers.get('trade_execution', 0),
            equity_curve=self.equity_curve,
            trade_history=self.trade_history,
            signal_history=self.signal_history,
            risk_history=self.risk_history,
            performance_by_pair=dict(self.performance_by_pair),
            performance_by_timeframe=dict(self.performance_by_timeframe),
            performance_by_signal_type=dict(self.performance_by_signal_type),
            parameter_set=parameters,
            start_date=start_date,
            end_date=end_date,
            initial_balance=float(self.initial_balance),
            final_balance=float(self.current_balance),
            debug_logs=self.debug_logs,
            error_logs=self.error_logs,
            warnings=self.warnings,
            execution_summary=execution_summary
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.equity_curve:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins."""
        if not self.trade_history:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trade_history:
            if trade.pnl and trade.pnl > 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses."""
        if not self.trade_history:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trade_history:
            if trade.pnl and trade.pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def generate_debug_report(self, result: DebugBacktestResult, output_dir: str = "debug_reports") -> str:
        """Generate comprehensive debug report."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"debug_report_{timestamp}.json"
        
        # Convert result to dict for JSON serialization
        report_data = asdict(result)
        
        # Add additional analysis
        report_data['analysis'] = self._generate_analysis(result)
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self._log_debug(f"Debug report saved to {report_file}", "INFO")
        return str(report_file)
    
    def _generate_analysis(self, result: DebugBacktestResult) -> Dict[str, Any]:
        """Generate additional analysis for the report."""
        analysis = {
            'performance_insights': {},
            'risk_analysis': {},
            'signal_analysis': {},
            'recommendations': []
        }
        
        # Performance insights
        if result.total_trades > 0:
            analysis['performance_insights'] = {
                'avg_trade_return': result.total_return / result.total_trades,
                'risk_reward_ratio': abs(result.avg_win / max(result.avg_loss, 0.01)),
                'profit_factor_quality': 'Excellent' if result.profit_factor > 2.0 else 'Good' if result.profit_factor > 1.5 else 'Poor',
                'sharpe_ratio_quality': 'Excellent' if result.sharpe_ratio > 2.0 else 'Good' if result.sharpe_ratio > 1.0 else 'Poor'
            }
        
        # Risk analysis
        analysis['risk_analysis'] = {
            'max_drawdown_severity': 'High' if result.max_drawdown > 20 else 'Medium' if result.max_drawdown > 10 else 'Low',
            'consecutive_losses_risk': 'High' if result.consecutive_losses > 5 else 'Medium' if result.consecutive_losses > 3 else 'Low',
            'signal_quality': result.signals_acted_upon / max(result.total_signals_generated, 1)
        }
        
        # Signal analysis
        analysis['signal_analysis'] = {
            'signal_efficiency': result.signals_acted_upon / max(result.total_signals_generated, 1),
            'risk_check_pass_rate': result.risk_checks_passed / max(result.risk_checks_passed + result.risk_checks_failed, 1)
        }
        
        # Recommendations
        recommendations = []
        if result.win_rate < 50:
            recommendations.append("Consider improving entry criteria to increase win rate")
        if result.max_drawdown > 15:
            recommendations.append("Implement stricter risk management to reduce drawdown")
        if result.profit_factor < 1.5:
            recommendations.append("Optimize exit strategies to improve profit factor")
        if result.consecutive_losses > 5:
            recommendations.append("Add filters to avoid trading during unfavorable conditions")
        
        analysis['recommendations'] = recommendations
        
        return analysis
