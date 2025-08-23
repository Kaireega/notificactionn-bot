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
from ..core.advanced_risk_manager import AdvancedRiskManager
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
        self.risk_manager = AdvancedRiskManager(config)
        self.broker = SimulationBroker(config)
        self.performance_metrics = PerformanceMetrics()
        
        # Backtest state
        self.current_balance = config.backtesting.initial_balance
        self.initial_balance = config.backtesting.initial_balance
        self.equity_curve = []
        self.trade_history = []
        self.open_positions = {}
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
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
            self.equity_curve.append(self.current_balance)
        
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
        self.equity_curve = [self.initial_balance]
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
        grouped_data = {}
        for timestamp, pair, timeframe, candle in all_candles:
            if timestamp not in grouped_data:
                grouped_data[timestamp] = {}
            if pair not in grouped_data[timestamp]:
                grouped_data[timestamp][pair] = {}
            if timeframe not in grouped_data[timestamp][pair]:
                grouped_data[timestamp][pair][timeframe] = []
            grouped_data[timestamp][pair][timeframe].append(candle)
        
        self.logger.info(f"Grouped data: {len(grouped_data)} unique timestamps")
        return grouped_data
    
    async def _process_timestamp(
        self, 
        timestamp: datetime, 
        candles_by_pair: Dict[str, Dict[TimeFrame, List[CandleData]]]
    ):
        """Process all candles for a specific timestamp."""
        
        # Update open positions (check for stop loss/take profit)
        await self._update_positions(timestamp, candles_by_pair)
        
        # Update rolling windows with new candles
        for pair, timeframes in candles_by_pair.items():
            if pair not in self.candle_windows:
                self.candle_windows[pair] = {}
            
            for timeframe, candles in timeframes.items():
                if timeframe not in self.candle_windows[pair]:
                    self.candle_windows[pair][timeframe] = []
                
                # Add new candles to the window
                self.candle_windows[pair][timeframe].extend(candles)
                
                # Keep only the last 100 candles to prevent memory issues
                if len(self.candle_windows[pair][timeframe]) > 100:
                    self.candle_windows[pair][timeframe] = self.candle_windows[pair][timeframe][-100:]
        
        # Analyze each pair
        for pair, timeframes in candles_by_pair.items():
            if pair not in self.config.trading_pairs:
                continue
            
            # Check if we can open new positions
            if len(self.open_positions) >= self.config.risk_management.max_open_trades:
                continue
            
            # Get market context
            market_context = self._create_market_context(timeframes)
            
            # Use rolling windows for technical analysis
            rolling_timeframes = {}
            for timeframe in timeframes.keys():
                if pair in self.candle_windows and timeframe in self.candle_windows[pair]:
                    rolling_timeframes[timeframe] = self.candle_windows[pair][timeframe]
            
            # Run technical analysis with rolling windows
            recommendation, indicators = await self.technical_layer.analyze_multiple_timeframes(
                pair, rolling_timeframes, market_context
            )
            
            if recommendation and indicators:
                self.logger.info(f"📊 Generated recommendation for {pair}: {recommendation.signal}")
                
                # Get current price
                current_price = self._get_current_price(timeframes.get(TimeFrame.M5, []))
                
                # Make decision
                decision = await self.decision_layer.make_technical_decision(
                    pair, {TimeFrame.M5: indicators}, market_context, current_price, timeframes
                )
                
                if decision and decision.approved:
                    self.logger.info(f"✅ Trade approved for {pair}: {decision.position_size}")
                    # Execute trade
                    await self._execute_trade(decision, timestamp, current_price)
                else:
                    self.logger.info(f"❌ Trade rejected for {pair}")
            else:
                self.logger.info(f"📊 No recommendation generated for {pair}")
    
    async def _update_positions(self, timestamp: datetime, candles_by_pair: Dict[str, Dict[TimeFrame, List[CandleData]]]):
        """Update open positions and check for exits."""
        
        positions_to_close = []
        
        for pair, position in self.open_positions.items():
            if pair in candles_by_pair:
                current_price = self._get_current_price(candles_by_pair[pair].get(TimeFrame.M5, []))
                
                # Check stop loss
                if position['signal'] == TradeSignal.BUY and current_price <= position['stop_loss']:
                    positions_to_close.append((pair, 'stop_loss', current_price))
                elif position['signal'] == TradeSignal.SELL and current_price >= position['stop_loss']:
                    positions_to_close.append((pair, 'stop_loss', current_price))
                
                # Check take profit
                elif position['signal'] == TradeSignal.BUY and current_price >= position['take_profit']:
                    positions_to_close.append((pair, 'take_profit', current_price))
                elif position['signal'] == TradeSignal.SELL and current_price <= position['take_profit']:
                    positions_to_close.append((pair, 'take_profit', current_price))
        
        # Close positions
        for pair, exit_reason, exit_price in positions_to_close:
            await self._close_position(pair, exit_reason, exit_price, timestamp)
    
    async def _execute_trade(self, decision: TradeDecision, timestamp: datetime, current_price: Decimal):
        """Execute a trade through the simulation broker."""
        
        try:
            self.logger.info(f"🚀 Executing trade: {decision.recommendation.pair} {decision.recommendation.signal.value}")
            
            # Use position size from decision
            position_size = float(decision.position_size)
            self.logger.info(f"📊 Position size: {position_size}")
            
            # Execute through broker
            trade_id = await self.broker.execute_trade(
                pair=decision.recommendation.pair,
                signal=decision.recommendation.signal,
                size=position_size,
                entry_price=current_price,
                stop_loss=decision.modified_stop_loss,
                take_profit=decision.modified_take_profit,
                timestamp=timestamp
            )
            
            self.logger.info(f"✅ Trade executed with ID: {trade_id}")
            
            # Record position
            self.open_positions[decision.recommendation.pair] = {
                'trade_id': trade_id,
                'signal': decision.recommendation.signal,
                'size': position_size,
                'entry_price': current_price,
                'stop_loss': decision.modified_stop_loss,
                'take_profit': decision.modified_take_profit,
                'entry_time': timestamp
            }
            
            self.logger.info(f"📈 Opened position: {decision.recommendation.pair} "
                            f"{decision.recommendation.signal.value} at {current_price}")
            
        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {e}")
            import traceback
            traceback.print_exc()
    
    async def _close_position(self, pair: str, exit_reason: str, exit_price: Decimal, timestamp: datetime):
        """Close an open position."""
        
        if pair not in self.open_positions:
            return
        
        position = self.open_positions[pair]
        
        try:
            # Convert position size to Decimal for consistent calculations
            position_size = Decimal(str(position['size']))
            
            # Calculate P&L
            if position['signal'] == TradeSignal.BUY:
                pnl = (exit_price - position['entry_price']) * position_size
            else:
                pnl = (position['entry_price'] - exit_price) * position_size
            
            # Apply broker fees
            pnl -= Decimal(str(self.broker.calculate_fees(position['size'], position['entry_price'])))
            pnl -= Decimal(str(self.broker.calculate_fees(position['size'], exit_price)))
            
            # Update balance - ensure both are Decimal types
            self.current_balance = Decimal(str(self.current_balance)) + pnl
            self.total_pnl = Decimal(str(self.total_pnl)) + pnl
            
            # Record trade
            trade_record = {
                'pair': pair,
                'signal': position['signal'].value,
                'entry_price': float(position['entry_price']),
                'exit_price': float(exit_price),
                'size': position['size'],
                'pnl': pnl,
                'entry_time': position['entry_time'],
                'exit_time': timestamp,
                'duration_minutes': (timestamp - position['entry_time']).total_seconds() / 60,
                'exit_reason': exit_reason
            }
            
            self.trade_history.append(trade_record)
            
            # Update statistics
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Remove from open positions
            del self.open_positions[pair]
            
            self.logger.debug(f"Closed position: {pair} {exit_reason} at {exit_price}, P&L: {pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    def _create_market_context(self, timeframes: Dict[TimeFrame, List[CandleData]]) -> MarketContext:
        """Create market context from timeframe data."""
        
        # Calculate basic market context
        primary_candles = timeframes.get(TimeFrame.M5, [])
        if not primary_candles:
            primary_candles = list(timeframes.values())[0] if timeframes else []
        
        if len(primary_candles) < 2:
            return MarketContext(
                condition=MarketCondition.RANGING,
                volatility=Decimal('0.001'),
                trend_strength=Decimal('0.0'),
                news_sentiment=Decimal('0.0')
            )
        
        # Calculate volatility (ATR-like)
        high_low_ranges = []
        for i in range(1, min(len(primary_candles), 14)):
            high_low_ranges.append(primary_candles[i].high - primary_candles[i].low)
        
        volatility = sum(high_low_ranges) / len(high_low_ranges) if high_low_ranges else Decimal('0.001')
        
        # Calculate trend strength
        if len(primary_candles) >= 20:
            recent_avg = sum(c.close for c in primary_candles[-10:]) / 10
            older_avg = sum(c.close for c in primary_candles[-20:-10]) / 10
            trend_strength = abs(recent_avg - older_avg) / older_avg
        else:
            trend_strength = Decimal('0.0')
        
        # Determine market condition
        if trend_strength > Decimal('0.01'):
            condition = MarketCondition.TRENDING
        elif volatility > Decimal('0.002'):
            condition = MarketCondition.NEWS_REACTIONARY
        else:
            condition = MarketCondition.RANGING
        
        return MarketContext(
            condition=condition,
            volatility=volatility,
            trend_strength=trend_strength,
            news_sentiment=Decimal('0.0')
        )
    
    def _get_current_price(self, candles: List[CandleData]) -> Decimal:
        """Get current price from the latest candle."""
        if not candles:
            return Decimal('0')
        
        latest_candle = candles[-1]
        return (latest_candle.high + latest_candle.low) / 2
    
    def _calculate_backtest_results(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        parameters: Dict[str, Any]
    ) -> BacktestResult:
        """Calculate comprehensive backtest results."""
        
        # Calculate basic metrics
        win_rate = self.winning_trades / max(1, self.total_trades)
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        
        # Calculate profit factor
        winning_pnl = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        losing_pnl = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        profit_factor = winning_pnl / max(1, losing_pnl)
        
        # Calculate drawdown
        max_drawdown = self.performance_metrics.calculate_max_drawdown(self.equity_curve)
        
        # Calculate Sharpe ratio
        returns = self.performance_metrics.calculate_returns(self.equity_curve)
        sharpe_ratio = self.performance_metrics.calculate_sharpe_ratio(returns)
        
        # Calculate trade statistics
        if self.trade_history:
            avg_trade_duration = sum(t['duration_minutes'] for t in self.trade_history) / len(self.trade_history)
            avg_win = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0) / max(1, self.winning_trades)
            avg_loss = sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0) / max(1, self.losing_trades)
            largest_win = max((t['pnl'] for t in self.trade_history), default=0)
            largest_loss = min((t['pnl'] for t in self.trade_history), default=0)
        else:
            avg_trade_duration = avg_win = avg_loss = largest_win = largest_loss = 0
        
        # Calculate consecutive wins/losses
        consecutive_wins = self.performance_metrics.calculate_consecutive_wins(self.trade_history)
        consecutive_losses = self.performance_metrics.calculate_consecutive_losses(self.trade_history)
        
        return BacktestResult(
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration=avg_trade_duration,
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
            initial_balance=self.initial_balance,
            final_balance=self.current_balance
        )
