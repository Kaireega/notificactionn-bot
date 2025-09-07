"""
Comprehensive Backtesting Engine
Tests trading strategies on historical data with proper risk management and performance tracking.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

from ..core.models import (
    TradeDecision, TradeRecommendation, CandleData, TimeFrame, 
    TradeSignal, MarketContext, TechnicalIndicators, MarketCondition
)
from ..utils.config import Config
from ..utils.logger import get_logger
from ..ai.technical_analysis_layer import TechnicalAnalysisLayer
from ..decision.technical_decision_layer import TechnicalDecisionLayer
from ..data.data_layer import DataLayer


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    initial_balance: float = 0.0
    final_balance: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    start_date: datetime = field(default_factory=lambda: datetime.now())
    end_date: datetime = field(default_factory=lambda: datetime.now())


class BacktestEngine:
    """Comprehensive backtesting engine for trading strategies."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.data_layer = DataLayer(config)
        self.technical_layer = TechnicalAnalysisLayer(config)
        self.decision_layer = TechnicalDecisionLayer(config)
        
        # Backtest state
        self.current_balance: float = 0.0
        self.initial_balance: float = 0.0
        self.peak_balance: float = 0.0
        self.open_positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.equity_curve: List[float] = []
        self.drawdown_curve: List[float] = []
        self.daily_pnl: Dict[str, float] = {}
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float = 10000.0,
        pairs: List[str] = None,
        risk_percentage: float = None
    ) -> BacktestResult:
        """Run comprehensive backtest with account balance integration."""
        
        self.logger.info(f"🚀 Starting backtest from {start_date} to {end_date}")
        self.logger.info(f"💰 Initial balance: ${initial_balance:,.2f}")
        
        # Initialize backtest state
        self.current_balance = Decimal(str(initial_balance))
        self.initial_balance = Decimal(str(initial_balance))
        self.peak_balance = Decimal(str(initial_balance))
        self.open_positions = {}
        self.trade_history = []
        self.equity_curve = [initial_balance]
        self.drawdown_curve = [0.0]
        self.daily_pnl = {}
        
        # Reset performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
        # Use provided pairs or config default
        if pairs is None:
            pairs = self.config.trading_pairs
            
        # Override risk percentage if provided
        if risk_percentage is not None:
            original_risk = self.config.trading.risk_percentage
            self.config.trading.risk_percentage = risk_percentage
            self.logger.info(f"📊 Using custom risk percentage: {risk_percentage}%")
        
        try:
            # Load historical data
            historical_data = await self._load_historical_data(start_date, end_date, pairs)
            
            # Run simulation
            result = await self._run_simulation(historical_data, start_date, end_date)
            
            # Calculate final metrics
            self._calculate_performance_metrics(result)
            
            # Generate detailed report
            self._generate_backtest_report(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Backtest failed: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            # Restore original risk percentage
            if risk_percentage is not None:
                self.config.trading.risk_percentage = original_risk
    
    async def _load_historical_data(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        pairs: List[str]
    ) -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
        """Load historical data for backtesting."""
        
        self.logger.info(f"📊 Loading historical data for {len(pairs)} pairs...")
        
        historical_data = {}
        
        for pair in pairs:
            historical_data[pair] = {}
            for timeframe in [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15]:
                try:
                    # Load data from CSV or database
                    candles = await self._load_candles_from_source(pair, timeframe, start_date, end_date)
                    historical_data[pair][timeframe] = candles
                    self.logger.debug(f"📈 Loaded {len(candles)} candles for {pair} {timeframe.value}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load data for {pair} {timeframe.value}: {e}")
                    historical_data[pair][timeframe] = []
        
        return historical_data
    
    async def _load_candles_from_source(
        self, 
        pair: str, 
        timeframe: TimeFrame, 
        start_date: datetime,
        end_date: datetime
    ) -> List[CandleData]:
        """Load candles from data source (CSV, database, or API)."""
        
        # Try to load from CSV first
        csv_path = f"data/historical/{pair}_{timeframe.value}.csv"
        
        try:
            if Path(csv_path).exists():
                return await self._load_from_csv(csv_path, start_date, end_date)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load from CSV {csv_path}: {e}")
        
        # Fallback to mock data for testing
        return self._generate_mock_data(pair, timeframe, start_date, end_date)
    
    async def _load_from_csv(self, csv_path: str, start_date: datetime, end_date: datetime) -> List[CandleData]:
        """Load candle data from CSV file."""
        
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date range
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        df = df[mask]
        
        candles = []
        for _, row in df.iterrows():
            candle = CandleData(
                timestamp=row['timestamp'],
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=row.get('volume', 0)
            )
            candles.append(candle)
        
        return candles
    
    def _generate_mock_data(
        self, 
        pair: str, 
        timeframe: TimeFrame, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[CandleData]:
        """Generate mock data for testing when real data is not available."""
        
        candles = []
        current_time = start_date
        
        # Generate realistic price movements
        base_price = 1.2000 if 'USD' in pair else 100.0
        price = base_price
        
        while current_time <= end_date:
            # Generate realistic price movement
            change = np.random.normal(0, 0.001)  # Small random change
            price += change
            
            # Ensure price stays reasonable
            if 'USD' in pair:
                price = max(0.5, min(2.0, price))
            else:
                price = max(50.0, min(200.0, price))
            
            # Create candle
            high = price + abs(np.random.normal(0, 0.0005))
            low = price - abs(np.random.normal(0, 0.0005))
            open_price = price + np.random.normal(0, 0.0002)
            close_price = price + np.random.normal(0, 0.0002)
            
            candle = CandleData(
                timestamp=current_time,
                open=Decimal(str(open_price)),
                high=Decimal(str(high)),
                low=Decimal(str(low)),
                close=Decimal(str(close_price)),
                volume=np.random.randint(1000, 10000)
            )
            candles.append(candle)
            
            # Move to next candle
            if timeframe == TimeFrame.M1:
                current_time += timedelta(minutes=1)
            elif timeframe == TimeFrame.M5:
                current_time += timedelta(minutes=5)
            elif timeframe == TimeFrame.M15:
                current_time += timedelta(minutes=15)
        
        return candles
    
    async def _run_simulation(
        self,
        historical_data: Dict[str, Dict[TimeFrame, List[CandleData]]],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Run the actual simulation."""
        
        result = BacktestResult()
        result.start_date = start_date
        result.end_date = end_date
        result.initial_balance = self.initial_balance
        
        current_date = start_date
        
        self.logger.info(f"🔄 Running simulation from {start_date} to {end_date}")
        
        while current_date <= end_date:
            # Process each pair
            for pair, timeframe_data in historical_data.items():
                # Get candles for current date
                current_candles = self._get_candles_for_date(timeframe_data, current_date)
                
                if not current_candles:
                    continue
                
                # Create market context
                market_context = self._create_market_context(current_candles)
                
                # Run technical analysis
                recommendation, primary_indicators = await self.technical_layer.analyze_multiple_timeframes(
                    pair, current_candles, market_context
                )
                
                if recommendation:
                    # Run decision making
                    current_price = self._get_current_price(current_candles[TimeFrame.M5])
                    
                    # Convert single indicators to dictionary format expected by decision layer
                    technical_indicators_dict = {TimeFrame.M5: primary_indicators}
                    
                    decision = await self.decision_layer.make_technical_decision(
                        pair, technical_indicators_dict, market_context, current_price, current_candles
                    )
                    
                    if decision and decision.approved:
                        # Execute trade
                        trade_result = self._execute_backtest_trade(decision, current_date, current_price)
                        if trade_result:
                            result.trades.append(trade_result)
                            self.trade_history.append(trade_result)
                
                # Update open positions
                self._update_open_positions(current_date, current_candles)
            
            # Update equity curve
            self._update_equity_curve(current_date)
            
            # Move to next interval (5 minutes)
            current_date += timedelta(minutes=5)
        
        # Calculate final results
        result.final_balance = self.current_balance
        result.total_return = float(self.current_balance - self.initial_balance)
        result.total_return_pct = (result.total_return / self.initial_balance) * 100
        result.max_drawdown = max(self.drawdown_curve)
        result.max_drawdown_pct = (result.max_drawdown / self.peak_balance) * 100
        result.trades = self.trade_history
        result.equity_curve = self.equity_curve
        result.drawdown_curve = self.drawdown_curve
        
        return result
    
    def _get_candles_for_date(
        self, 
        timeframe_data: Dict[TimeFrame, List[CandleData]], 
        target_date: datetime
    ) -> Dict[TimeFrame, List[CandleData]]:
        """Get candles up to the target date for each timeframe."""
        
        current_candles = {}
        
        for timeframe, all_candles in timeframe_data.items():
            # Get candles up to target date
            candles_up_to_date = [
                candle for candle in all_candles 
                if candle.timestamp <= target_date
            ]
            
            # Keep last 100 candles for analysis
            current_candles[timeframe] = candles_up_to_date[-100:] if len(candles_up_to_date) > 100 else candles_up_to_date
        
        return current_candles
    
    def _create_market_context(self, candles_by_timeframe: Dict[TimeFrame, List[CandleData]]) -> MarketContext:
        """Create market context from candle data."""
        
        # Use M5 candles for market context
        m5_candles = candles_by_timeframe.get(TimeFrame.M5, [])
        
        if not m5_candles:
            return MarketContext(
                condition=MarketCondition.NORMAL,
                volatility=0.0,
                trend_strength=0.0,
                news_sentiment=0.0
            )
        
        # Calculate basic market metrics
        prices = [float(candle.close) for candle in m5_candles[-20:]]  # Last 20 candles
        
        # Calculate volatility (standard deviation of returns)
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
        volatility = np.std(returns) if len(returns) > 1 else 0.0
        
        # Calculate trend strength (linear regression R-squared)
        if len(prices) > 5:
            x = np.arange(len(prices))
            slope, intercept = np.polyfit(x, prices, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((prices - y_pred) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)
            trend_strength = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            trend_strength = 0.0
        
        # Determine market condition
        if volatility > 0.002:  # High volatility
            condition = MarketCondition.NEWS_REACTIONARY
        elif trend_strength > 0.7:  # Strong trend
            condition = MarketCondition.BREAKOUT
        elif volatility < 0.0005:  # Low volatility
            condition = MarketCondition.RANGING
        else:
            condition = MarketCondition.UNKNOWN
        
        return MarketContext(
            condition=condition,
            volatility=volatility,
            trend_strength=trend_strength,
            news_sentiment=0.0  # Mock data doesn't include news
        )
    
    def _get_current_price(self, candles: List[CandleData]) -> Decimal:
        """Get current price from the latest candle."""
        if not candles:
            return Decimal('0')
        
        latest_candle = candles[-1]
        return (latest_candle.high + latest_candle.low) / 2  # Use typical price
    
    def _execute_backtest_trade(
        self, 
        decision: TradeDecision, 
        execution_date: datetime,
        current_price: Decimal
    ) -> Optional[Dict]:
        """Execute a trade in the backtest environment."""
        
        try:
            # Calculate position size based on risk percentage
            risk_amount = self.current_balance * Decimal(str(self.config.trading.risk_percentage / 100))
            
            # Calculate units based on stop loss distance
            entry_price = float(decision.recommendation.entry_price)
            stop_loss = float(decision.modified_stop_loss)
            
            if stop_loss == 0 or entry_price == 0:
                self.logger.warning(f"⚠️ Invalid prices for trade: entry={entry_price}, stop={stop_loss}")
                return None
            
            # Calculate pip value (assuming standard lot size)
            pip_distance = abs(entry_price - stop_loss)
            if pip_distance == 0:
                self.logger.warning(f"⚠️ Zero pip distance for trade")
                return None
            
            # Calculate position size in units (convert pip_distance to Decimal for division)
            units = float(risk_amount / Decimal(str(pip_distance)))
            
            # Apply position size limits
            max_units = float(self.current_balance * Decimal(str(self.config.risk_management.max_position_size / 100)))
            units = min(units, max_units)
            
            # Create trade record
            trade = {
                'id': f"backtest_{len(self.trade_history) + 1}",
                'pair': decision.recommendation.pair,
                'signal': decision.recommendation.signal.value,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': float(decision.modified_take_profit) if decision.modified_take_profit else None,
                'units': units,
                'risk_amount': risk_amount,
                'entry_time': execution_date,
                'status': 'OPEN'
            }
            
            # Store open position
            self.open_positions[decision.recommendation.pair] = trade
            
            self.logger.info(f"📈 Backtest trade opened: {trade['pair']} {trade['signal']} "
                           f"@ {trade['entry_price']:.5f}, units: {trade['units']:.2f}")
            
            return trade
            
        except Exception as e:
            self.logger.error(f"❌ Error executing backtest trade: {e}")
            return None
    
    def _update_open_positions(self, current_date: datetime, candles_by_timeframe: Dict[TimeFrame, List[CandleData]]):
        """Update open positions and check for exits."""
        
        m5_candles = candles_by_timeframe.get(TimeFrame.M5, [])
        if not m5_candles:
            return
        
        current_price = float(self._get_current_price(m5_candles))
        
        positions_to_close = []
        
        for pair, position in self.open_positions.items():
            if position['status'] != 'OPEN':
                continue
            
            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            signal = position['signal']
            
            # Check for stop loss
            if signal == 'BUY' and current_price <= stop_loss:
                position['exit_price'] = stop_loss
                position['exit_reason'] = 'STOP_LOSS'
                position['exit_time'] = current_date
                position['status'] = 'CLOSED'
                positions_to_close.append(position)
                
            elif signal == 'SELL' and current_price >= stop_loss:
                position['exit_price'] = stop_loss
                position['exit_reason'] = 'STOP_LOSS'
                position['exit_time'] = current_date
                position['status'] = 'CLOSED'
                positions_to_close.append(position)
            
            # Check for take profit
            elif take_profit and signal == 'BUY' and current_price >= take_profit:
                position['exit_price'] = take_profit
                position['exit_reason'] = 'TAKE_PROFIT'
                position['exit_time'] = current_date
                position['status'] = 'CLOSED'
                positions_to_close.append(position)
                
            elif take_profit and signal == 'SELL' and current_price <= take_profit:
                position['exit_price'] = take_profit
                position['exit_reason'] = 'TAKE_PROFIT'
                position['exit_time'] = current_date
                position['status'] = 'CLOSED'
                positions_to_close.append(position)
        
        # Process closed positions
        for position in positions_to_close:
            self._process_closed_position(position)
            del self.open_positions[position['pair']]
    
    def _process_closed_position(self, position: Dict):
        """Process a closed position and update account balance."""
        
        entry_price = position['entry_price']
        exit_price = position['exit_price']
        units = position['units']
        signal = position['signal']
        
        # Calculate P&L
        if signal == 'BUY':
            pnl = (exit_price - entry_price) * units
        else:  # SELL
            pnl = (entry_price - exit_price) * units
        
        # Update account balance (convert pnl to Decimal)
        self.current_balance += Decimal(str(pnl))
        
        # Update performance tracking
        self.total_trades += 1
        self.total_pnl += float(pnl)
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update position with P&L
        position['pnl'] = pnl
        position['balance_after'] = self.current_balance
        
        # Update peak balance
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        self.logger.info(f"📊 Position closed: {position['pair']} {position['signal']} "
                        f"P&L: ${pnl:.2f}, Balance: ${self.current_balance:.2f}")
    
    def _update_equity_curve(self, current_date: datetime):
        """Update equity curve and drawdown tracking."""
        
        # Calculate current equity (balance + unrealized P&L)
        current_equity = self.current_balance
        
        # Add unrealized P&L from open positions
        for position in self.open_positions.values():
            if position['status'] == 'OPEN':
                # Simplified unrealized P&L calculation
                # In a real implementation, you'd use current market prices
                current_equity += position.get('unrealized_pnl', 0)
        
        self.equity_curve.append(current_equity)
        
        # Calculate drawdown
        if current_equity > self.peak_balance:
            self.peak_balance = current_equity
        
        drawdown = self.peak_balance - current_equity
        self.drawdown_curve.append(drawdown)
    
    def _calculate_performance_metrics(self, result: BacktestResult):
        """Calculate comprehensive performance metrics."""
        
        if not result.trades:
            self.logger.warning("⚠️ No trades executed during backtest")
            return
        
        # Basic metrics
        result.total_trades = len(result.trades)
        result.winning_trades = len([t for t in result.trades if t.get('pnl', 0) > 0])
        result.losing_trades = result.total_trades - result.winning_trades
        result.win_rate = result.winning_trades / result.total_trades if result.total_trades > 0 else 0
        
        # P&L metrics
        winning_pnl = sum(t.get('pnl', 0) for t in result.trades if t.get('pnl', 0) > 0)
        losing_pnl = abs(sum(t.get('pnl', 0) for t in result.trades if t.get('pnl', 0) < 0))
        
        result.avg_win = winning_pnl / result.winning_trades if result.winning_trades > 0 else 0
        result.avg_loss = losing_pnl / result.losing_trades if result.losing_trades > 0 else 0
        result.profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else float('inf')
        
        # Largest win/loss
        pnls = [t.get('pnl', 0) for t in result.trades]
        result.largest_win = max(pnls) if pnls else 0
        result.largest_loss = min(pnls) if pnls else 0
        
        # Sharpe ratio (simplified)
        if len(result.equity_curve) > 1:
            returns = [(result.equity_curve[i] / result.equity_curve[i-1]) - 1 
                      for i in range(1, len(result.equity_curve))]
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                result.sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        self.logger.info(f"📊 Backtest completed:")
        self.logger.info(f"   💰 Final Balance: ${result.final_balance:.2f}")
        self.logger.info(f"   📈 Total Return: {result.total_return_pct:.2f}%")
        self.logger.info(f"   📊 Win Rate: {result.win_rate:.1%}")
        self.logger.info(f"   📉 Max Drawdown: {result.max_drawdown_pct:.2f}%")
        self.logger.info(f"   📊 Profit Factor: {result.profit_factor:.2f}")
        self.logger.info(f"   📈 Sharpe Ratio: {result.sharpe_ratio:.2f}")
    
    def _generate_backtest_report(self, result: BacktestResult):
        """Generate detailed backtest report."""
        
        report = f"""
📊 BACKTEST REPORT
==================

💰 ACCOUNT PERFORMANCE:
   Initial Balance: ${result.initial_balance:,.2f}
   Final Balance: ${result.final_balance:,.2f}
   Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2f}%)
   Max Drawdown: ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)

📈 TRADING PERFORMANCE:
   Total Trades: {result.total_trades}
   Winning Trades: {result.winning_trades}
   Losing Trades: {result.losing_trades}
   Win Rate: {result.win_rate:.1%}
   Profit Factor: {result.profit_factor:.2f}
   Sharpe Ratio: {result.sharpe_ratio:.2f}

💰 P&L ANALYSIS:
   Average Win: ${result.avg_win:.2f}
   Average Loss: ${result.avg_loss:.2f}
   Largest Win: ${result.largest_win:.2f}
   Largest Loss: ${result.largest_loss:.2f}

⚙️ RISK MANAGEMENT:
   Risk per Trade: {self.config.trading.risk_percentage}%
   Max Position Size: {self.config.risk_management.max_position_size}%
   Max Daily Loss: {self.config.risk_management.max_daily_loss}%

📅 TEST PERIOD:
   Start: {result.start_date.strftime('%Y-%m-%d %H:%M')}
   End: {result.end_date.strftime('%Y-%m-%d %H:%M')}
   Duration: {(result.end_date - result.start_date).days} days
"""
        
        self.logger.info(report)
        
        # Save detailed report to file
        report_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.logger.info(f"📄 Detailed report saved to: {report_file}")


# Import path for compatibility
from pathlib import Path
