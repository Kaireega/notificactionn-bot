"""
Performance Tracker - Tracks trading performance metrics.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import statistics

from src.core.models import TradeDecision, PerformanceMetrics, TradeExecution
from src.utils.logger import get_logger


class PerformanceTracker:
    """Tracks and calculates trading performance metrics."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Performance data
        self._trades: List[TradeExecution] = []
        self._performance_metrics = PerformanceMetrics()
        self._last_calculation = datetime.utcnow()
        
        # Time periods for analysis
        self._periods = {
            'daily': timedelta(days=1),
            'weekly': timedelta(days=7),
            'monthly': timedelta(days=30)
        }
    
    def add_trade(self, trade_execution: TradeExecution) -> None:
        """Add a completed trade to the tracker."""
        self._trades.append(trade_execution)
        self._update_metrics()
    
    def get_performance_metrics(self, period: str = 'all') -> PerformanceMetrics:
        """Get performance metrics for the specified period."""
        if period == 'all':
            return self._performance_metrics
        
        # Filter trades by period
        cutoff_time = datetime.utcnow() - self._periods.get(period, timedelta(days=30))
        period_trades = [t for t in self._trades if t.execution_time >= cutoff_time]
        
        return self._calculate_metrics(period_trades)
    
    def get_win_rate(self, period: str = 'all') -> float:
        """Get win rate for the specified period."""
        metrics = self.get_performance_metrics(period)
        return metrics.win_rate
    
    def get_profit_factor(self, period: str = 'all') -> float:
        """Get profit factor for the specified period."""
        metrics = self.get_performance_metrics(period)
        return metrics.profit_factor
    
    def get_sharpe_ratio(self, period: str = 'all') -> float:
        """Get Sharpe ratio for the specified period."""
        metrics = self.get_performance_metrics(period)
        return metrics.sharpe_ratio
    
    def get_max_drawdown(self, period: str = 'all') -> Decimal:
        """Get maximum drawdown for the specified period."""
        metrics = self.get_performance_metrics(period)
        return metrics.max_drawdown
    
    def get_trade_summary(self, period: str = 'all') -> Dict[str, Any]:
        """Get a summary of trading performance."""
        metrics = self.get_performance_metrics(period)
        
        return {
            'total_trades': metrics.total_trades,
            'winning_trades': metrics.winning_trades,
            'losing_trades': metrics.losing_trades,
            'win_rate': f"{metrics.win_rate:.2%}",
            'total_profit': float(metrics.total_profit),
            'total_loss': float(metrics.total_loss),
            'net_profit': float(metrics.net_profit),
            'average_win': float(metrics.average_win),
            'average_loss': float(metrics.average_loss),
            'profit_factor': metrics.profit_factor,
            'max_drawdown': float(metrics.max_drawdown),
            'sharpe_ratio': metrics.sharpe_ratio
        }
    
    async def get_daily_metrics(self) -> PerformanceMetrics:
        """Get daily performance metrics (async wrapper for compatibility)."""
        return self.get_performance_metrics('daily')
    
    def _update_metrics(self) -> None:
        """Update performance metrics."""
        self._performance_metrics = self._calculate_metrics(self._trades)
        self._last_calculation = datetime.utcnow()
    
    def _calculate_metrics(self, trades: List[TradeExecution]) -> PerformanceMetrics:
        """Calculate performance metrics from trades."""
        if not trades:
            return PerformanceMetrics()
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if self._calculate_trade_pnl(t) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate profit/loss
        profits = [self._calculate_trade_pnl(t) for t in trades if self._calculate_trade_pnl(t) > 0]
        losses = [self._calculate_trade_pnl(t) for t in trades if self._calculate_trade_pnl(t) < 0]
        
        total_profit = sum(profits) if profits else Decimal('0')
        total_loss = abs(sum(losses)) if losses else Decimal('0')
        net_profit = total_profit - total_loss
        
        # Calculate averages
        average_win = total_profit / len(profits) if profits else Decimal('0')
        average_loss = total_loss / len(losses) if losses else Decimal('0')
        
        # Calculate profit factor
        profit_factor = float(total_profit / total_loss) if total_loss > 0 else float('inf')
        
        # Calculate maximum drawdown
        max_drawdown = self._calculate_max_drawdown(trades)
        
        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(trades)
        
        # Set time period
        if trades:
            period_start = min(t.execution_time for t in trades)
            period_end = max(t.execution_time for t in trades)
        else:
            period_start = datetime.utcnow()
            period_end = datetime.utcnow()
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            period_start=period_start,
            period_end=period_end
        )
    
    def _calculate_trade_pnl(self, trade: TradeExecution) -> Decimal:
        """Calculate profit/loss for a trade."""
        try:
            # This is a simplified calculation
            # In a real implementation, you'd get the actual P&L from the broker
            entry_price = trade.trade_decision.recommendation.entry_price
            exit_price = trade.execution_price
            
            if trade.trade_decision.recommendation.signal.value == 'buy':
                return exit_price - entry_price
            else:
                return entry_price - exit_price
        except Exception:
            return Decimal('0')
    
    def _calculate_max_drawdown(self, trades: List[TradeExecution]) -> Decimal:
        """Calculate maximum drawdown."""
        if not trades:
            return Decimal('0')
        
        # Sort trades by execution time
        sorted_trades = sorted(trades, key=lambda t: t.execution_time)
        
        peak = Decimal('0')
        max_drawdown = Decimal('0')
        running_balance = Decimal('0')
        
        for trade in sorted_trades:
            pnl = self._calculate_trade_pnl(trade)
            running_balance += pnl
            
            if running_balance > peak:
                peak = running_balance
            
            drawdown = peak - running_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, trades: List[TradeExecution]) -> float:
        """Calculate Sharpe ratio (simplified)."""
        if not trades:
            return 0.0
        
        # Calculate returns
        returns = []
        for trade in trades:
            pnl = self._calculate_trade_pnl(trade)
            # Convert to percentage return (simplified)
            entry_price = trade.trade_decision.recommendation.entry_price
            if entry_price > 0:
                returns.append(float(pnl / entry_price))
        
        if not returns:
            return 0.0
        
        # Calculate Sharpe ratio
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.0
        
        if std_return == 0:
            return 0.0
        
        # Assuming risk-free rate of 0 for simplicity
        sharpe_ratio = mean_return / std_return
        
        return sharpe_ratio
    
    def get_recent_trades(self, limit: int = 10) -> List[TradeExecution]:
        """Get the most recent trades."""
        sorted_trades = sorted(self._trades, key=lambda t: t.execution_time, reverse=True)
        return sorted_trades[:limit]
    
    def get_trades_by_pair(self, pair: str) -> List[TradeExecution]:
        """Get all trades for a specific pair."""
        return [t for t in self._trades if t.trade_decision.recommendation.pair == pair]
    
    def clear_old_data(self, days: int = 90) -> None:
        """Clear old trade data."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        self._trades = [t for t in self._trades if t.execution_time >= cutoff_time]
        self._update_metrics()
    
    async def start(self) -> None:
        """Start the performance tracker."""
        self.logger.info("Performance tracker started")
    
    async def close(self) -> None:
        """Close the performance tracker."""
        self.logger.info("Performance tracker closed")
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        self._trades = []
        self._performance_metrics = PerformanceMetrics()
        self._last_calculation = datetime.utcnow() 