"""
Backtesting Engine - Comprehensive backtesting framework for the trading bot.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json

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
class BacktestResult:
    """Results from a backtest run."""
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
    equity_curve: List[float]
    trade_history: List[Dict[str, Any]]
    parameter_set: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float


class BacktestEngine:
    """Comprehensive backtesting engine for the trading bot."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
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
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal('0.0')
        
    async def run_backtest(
        self,
        historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]],
        start_date: datetime,
        end_date: datetime,
        parameters: Optional[Dict[str, Any]] = None
    ) -> BacktestResult:
        """Run a complete backtest with the given parameters."""
        
        self.logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Reset state
        self._reset_backtest_state()
        
        # Apply custom parameters if provided
        if parameters:
            self._apply_parameters(parameters)
        
        # Ensure initial balance is Decimal
        self.current_balance = Decimal(str(self.current_balance))
        self.initial_balance = Decimal(str(self.initial_balance))
        
        # Sort all candles by timestamp
        all_candles = self._prepare_historical_data(historical_data, start_date, end_date)
        
        # Process each candle
        for timestamp, candles_by_pair in all_candles.items():
            await self._process_timestamp(timestamp, candles_by_pair)
            
            # Update equity curve
            self.equity_curve.append(float(self.current_balance))
        
        # Close all remaining open positions at the end of backtest
        if self.open_positions:
            self.logger.info(f"Closing {len(self.open_positions)} remaining open positions")
            for pair, position in list(self.open_positions.items()):
                # Use the last known price to close the position
                last_candles = all_candles[list(all_candles.keys())[-1]]
                if pair in last_candles:
                    current_price = self._get_current_price(last_candles[pair].get(TimeFrame.M5, []))
                    await self._close_position(pair, 'end_of_backtest', current_price, list(all_candles.keys())[-1])
        
        # Calculate final results
        result = self._calculate_backtest_results(start_date, end_date, parameters or {})
        
        self.logger.info(f"Backtest completed: {result.total_trades} trades, "
                        f"Win rate: {result.win_rate:.2%}, "
                        f"Return: {result.total_return:.2%}")
        
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
        # Initialize rolling windows for each pair and timeframe
        self.candle_windows = {}
    
    def _apply_parameters(self, parameters: Dict[str, Any]):
        """Apply custom parameters to the trading system."""
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
        """Prepare historical data sorted by timestamp."""
        
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
        
        self.logger.info(f"Data preparation: {total_candles} total candles, {filtered_candles} within date range")
        
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
        
        return grouped_candles
    
    async def _process_timestamp(self, timestamp: datetime, candles_by_pair: Dict[str, Dict[TimeFrame, List[CandleData]]]):
        """Process all candles for a specific timestamp."""
        
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
                
                # Analyze technical indicators
                technical_indicators = {}
                for tf, candles in timeframes.items():
                    if len(candles) >= 20:  # Minimum candles for indicators
                        indicators = self.technical_layer.technical_analyzer.calculate_indicators(candles)
                        technical_indicators[tf] = indicators
                
                if not technical_indicators:
                    continue
                
                # Make trading decision
                decision = await self.decision_layer.make_technical_decision(
                    pair, technical_indicators, market_context, current_price, timeframes
                )
                
                if decision and decision.approved:
                    # Execute trade
                    await self._execute_trade(pair, decision, current_price, timestamp)
                
            except Exception as e:
                self.logger.error(f"Error processing {pair} at {timestamp}: {e}")
                continue
    
    def _create_market_context(self, timeframes: Dict[TimeFrame, List[CandleData]]) -> MarketContext:
        """Create market context from timeframe data."""
        # Simple market context - can be enhanced
        return MarketContext(
            condition=MarketCondition.UNKNOWN,
            volatility=0.002,
            trend_strength=0.5
        )
    
    def _get_current_price(self, candles: List[CandleData]) -> Decimal:
        """Get current price from the latest candle."""
        if not candles:
            return Decimal('0')
        return candles[-1].close
    
    async def _execute_trade(self, pair: str, decision: TradeDecision, current_price: Decimal, timestamp: datetime):
        """Execute a trade based on the decision."""
        try:
            # Calculate position size
            risk_amount = self.current_balance * (self.config.trading.risk_percentage / 100)
            position_size = risk_amount / abs(float(current_price - decision.modified_stop_loss))
            
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
                self.open_positions[pair] = {
                    'decision': decision,
                    'entry_price': current_price,
                    'entry_time': timestamp,
                    'position_size': position_size,
                    'stop_loss': decision.modified_stop_loss,
                    'take_profit': decision.modified_take_profit
                }
                
                self.logger.info(f"Opened {decision.recommendation.signal.value} position for {pair} "
                               f"at {current_price}, size: {position_size:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error executing trade for {pair}: {e}")
    
    async def _close_position(self, pair: str, reason: str, current_price: Decimal, timestamp: datetime):
        """Close an open position."""
        if pair not in self.open_positions:
            return
        
        position = self.open_positions[pair]
        entry_price = position['entry_price']
        position_size = position['position_size']
        
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
        
        # Record trade
        trade_record = {
            'pair': pair,
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'entry_price': float(entry_price),
            'exit_price': float(current_price),
            'position_size': float(position_size),
            'pnl': float(pnl),
            'return_pct': float(pnl / (entry_price * position_size) * 100),
            'reason': reason,
            'signal': position['decision'].recommendation.signal.value
        }
        self.trade_history.append(trade_record)
        
        # Remove from open positions
        del self.open_positions[pair]
        
        self.logger.info(f"Closed {pair} position: {pnl:.2f} P&L ({reason})")
    
    def _calculate_backtest_results(self, start_date: datetime, end_date: datetime, parameters: Dict[str, Any]) -> BacktestResult:
        """Calculate comprehensive backtest results."""
        
        # Basic metrics
        total_return = float(self.current_balance - self.initial_balance) / float(self.initial_balance) * 100
        win_rate = self.winning_trades / max(self.total_trades, 1) * 100
        
        # Calculate profit factor
        total_wins = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        total_losses = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        profit_factor = total_wins / max(total_losses, 0.01)
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Calculate Sharpe ratio (simplified)
        if len(self.trade_history) > 1:
            returns = [t['return_pct'] for t in self.trade_history]
            sharpe_ratio = np.mean(returns) / max(np.std(returns), 0.01) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Calculate average trade duration
        if self.trade_history:
            durations = [(t['exit_time'] - t['entry_time']).total_seconds() / 3600 for t in self.trade_history]
            avg_duration = np.mean(durations)
        else:
            avg_duration = 0.0
        
        # Calculate other metrics
        if self.trade_history:
            wins = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
            losses = [t['pnl'] for t in self.trade_history if t['pnl'] < 0]
            
            avg_win = np.mean(wins) if wins else 0.0
            avg_loss = np.mean(losses) if losses else 0.0
            largest_win = max(wins) if wins else 0.0
            largest_loss = min(losses) if losses else 0.0
        else:
            avg_win = avg_loss = largest_win = largest_loss = 0.0
        
        # Calculate consecutive wins/losses
        consecutive_wins = self._calculate_consecutive_wins()
        consecutive_losses = self._calculate_consecutive_losses()
        
        return BacktestResult(
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
            equity_curve=self.equity_curve,
            trade_history=self.trade_history,
            parameter_set=parameters,
            start_date=start_date,
            end_date=end_date,
            initial_balance=float(self.initial_balance),
            final_balance=float(self.current_balance)
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
            if trade['pnl'] > 0:
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
            if trade['pnl'] < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
