"""
Enhanced Exit Criteria - Smart exit strategies for different market conditions
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from ..core.models import TradeDecision, MarketContext, TechnicalIndicators
from ..utils.logger import get_logger


class EnhancedExitCriteria:
    """Enhanced exit criteria with market condition specific strategies."""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Exit thresholds
        self.profit_target_multiplier = 2.0  # Exit at 2x ATR profit
        self.loss_cut_multiplier = 1.5  # Exit at 1.5x ATR loss
        self.time_based_exit_hours = 4  # Maximum hold time
        
        # Trailing stop settings
        self.trailing_stop_enabled = True
        self.trailing_stop_atr_multiplier = 1.5
        self.trailing_stop_activation_profit = 1.0  # Activate at 1x ATR profit
        
        # Market condition specific exit settings
        self.market_exit_settings = {
            'news_reactionary': {
                'max_hold_time_minutes': 90,
                'profit_target_multiplier': 1.5,
                'require_volume_decline': True
            },
            'reversal': {
                'max_hold_time_minutes': 180,
                'profit_target_multiplier': 2.5,
                'require_trend_confirmation': True
            },
            'breakout': {
                'max_hold_time_minutes': 240,
                'profit_target_multiplier': 3.0,
                'require_breakout_confirmation': True
            },
            'ranging': {
                'max_hold_time_minutes': 120,
                'profit_target_multiplier': 1.5,
                'require_range_boundary': True
            }
        }
        
    async def evaluate_exit_conditions(
        self,
        trade_decision: TradeDecision,
        current_price: Decimal,
        market_context: MarketContext,
        technical_indicators: Optional[TechnicalIndicators] = None,
        trade_duration_minutes: int = 0
    ) -> Dict[str, Any]:
        """Evaluate whether to exit a trade."""
        
        exit_result = {
            'should_exit': False,
            'reason': '',
            'exit_type': None,  # 'profit_target', 'stop_loss', 'trailing_stop', 'time_based', 'technical'
            'exit_price': current_price
        }
        
        try:
            # 1. Check profit target
            profit_check = self._check_profit_target(trade_decision, current_price)
            if profit_check['should_exit']:
                exit_result.update(profit_check)
                return exit_result
            
            # 2. Check stop loss
            stop_check = self._check_stop_loss(trade_decision, current_price)
            if stop_check['should_exit']:
                exit_result.update(stop_check)
                return exit_result
            
            # 3. Check trailing stop
            if self.trailing_stop_enabled:
                trailing_check = self._check_trailing_stop(trade_decision, current_price)
                if trailing_check['should_exit']:
                    exit_result.update(trailing_check)
                    return exit_result
            
            # 4. Check time-based exit
            time_check = self._check_time_based_exit(trade_decision, trade_duration_minutes)
            if time_check['should_exit']:
                exit_result.update(time_check)
                return exit_result
            
            # 5. Check technical exit signals
            if technical_indicators:
                technical_check = self._check_technical_exit_signals(
                    trade_decision, current_price, technical_indicators, market_context
                )
                if technical_check['should_exit']:
                    exit_result.update(technical_check)
                    return exit_result
            
            # 6. Check market condition specific exits
            condition_check = self._check_market_condition_exits(
                trade_decision, current_price, market_context, trade_duration_minutes
            )
            if condition_check['should_exit']:
                exit_result.update(condition_check)
                return exit_result
            
        except Exception as e:
            self.logger.error(f"Error in exit criteria evaluation: {e}")
            exit_result['reason'] = f'Exit evaluation error: {str(e)}'
        
        return exit_result
    
    def _check_profit_target(self, trade_decision: TradeDecision, current_price: Decimal) -> Dict[str, Any]:
        """Check if profit target has been reached."""
        recommendation = trade_decision.recommendation
        
        if recommendation.signal == 'buy':
            if current_price >= recommendation.take_profit:
                return {
                    'should_exit': True,
                    'reason': 'Profit target reached',
                    'exit_type': 'profit_target',
                    'exit_price': recommendation.take_profit
                }
        elif recommendation.signal == 'sell':
            if current_price <= recommendation.take_profit:
                return {
                    'should_exit': True,
                    'reason': 'Profit target reached',
                    'exit_type': 'profit_target',
                    'exit_price': recommendation.take_profit
                }
        
        return {'should_exit': False}
    
    def _check_stop_loss(self, trade_decision: TradeDecision, current_price: Decimal) -> Dict[str, Any]:
        """Check if stop loss has been hit."""
        recommendation = trade_decision.recommendation
        
        if recommendation.signal == 'buy':
            if current_price <= recommendation.stop_loss:
                return {
                    'should_exit': True,
                    'reason': 'Stop loss hit',
                    'exit_type': 'stop_loss',
                    'exit_price': recommendation.stop_loss
                }
        elif recommendation.signal == 'sell':
            if current_price >= recommendation.stop_loss:
                return {
                    'should_exit': True,
                    'reason': 'Stop loss hit',
                    'exit_type': 'stop_loss',
                    'exit_price': recommendation.stop_loss
                }
        
        return {'should_exit': False}
    
    def _check_trailing_stop(self, trade_decision: TradeDecision, current_price: Decimal) -> Dict[str, Any]:
        """Check trailing stop conditions."""
        # This would need to be implemented with position tracking
        # For now, return False
        return {'should_exit': False}
    
    def _check_time_based_exit(self, trade_decision: TradeDecision, trade_duration_minutes: int) -> Dict[str, Any]:
        """Check if trade should be closed based on time."""
        recommendation = trade_decision.recommendation
        
        # Get market condition specific hold time
        condition = recommendation.market_condition
        hold_times = self.config.trading.hold_time_settings.market_condition_hold_times.get(condition, [60, 240])
        max_hold_time = hold_times[1]
        
        if trade_duration_minutes >= max_hold_time:
            return {
                'should_exit': True,
                'reason': f'Maximum hold time reached ({max_hold_time} minutes)',
                'exit_type': 'time_based',
                'exit_price': current_price
            }
        
        return {'should_exit': False}
    
    def _check_technical_exit_signals(
        self,
        trade_decision: TradeDecision,
        current_price: Decimal,
        technical_indicators: TechnicalIndicators,
        market_context: MarketContext
    ) -> Dict[str, Any]:
        """Check for technical exit signals."""
        recommendation = trade_decision.recommendation
        
        # Check for signal reversal
        if recommendation.signal == 'buy':
            # Check if RSI is overbought
            if hasattr(technical_indicators, 'rsi') and technical_indicators.rsi > 70:
                return {
                    'should_exit': True,
                    'reason': 'RSI overbought - technical exit signal',
                    'exit_type': 'technical',
                    'exit_price': current_price
                }
            
            # Check if MACD is bearish
            if hasattr(technical_indicators, 'macd') and hasattr(technical_indicators, 'macd_signal'):
                if technical_indicators.macd < technical_indicators.macd_signal:
                    return {
                        'should_exit': True,
                        'reason': 'MACD bearish crossover - technical exit signal',
                        'exit_type': 'technical',
                        'exit_price': current_price
                    }
        
        elif recommendation.signal == 'sell':
            # Check if RSI is oversold
            if hasattr(technical_indicators, 'rsi') and technical_indicators.rsi < 30:
                return {
                    'should_exit': True,
                    'reason': 'RSI oversold - technical exit signal',
                    'exit_type': 'technical',
                    'exit_price': current_price
                }
            
            # Check if MACD is bullish
            if hasattr(technical_indicators, 'macd') and hasattr(technical_indicators, 'macd_signal'):
                if technical_indicators.macd > technical_indicators.macd_signal:
                    return {
                        'should_exit': True,
                        'reason': 'MACD bullish crossover - technical exit signal',
                        'exit_type': 'technical',
                        'exit_price': current_price
                    }
        
        return {'should_exit': False}
    
    def _check_market_condition_exits(
        self,
        trade_decision: TradeDecision,
        current_price: Decimal,
        market_context: MarketContext,
        trade_duration_minutes: int
    ) -> Dict[str, Any]:
        """Check market condition specific exit conditions."""
        recommendation = trade_decision.recommendation
        condition = recommendation.market_condition
        
        if condition == 'news_reactionary':
            # Exit news trades quickly if they stall
            if trade_duration_minutes > 30 and trade_duration_minutes < 60:
                # Check if price has moved less than 0.1% in the last 10 minutes
                # This would need price history tracking
                pass
        
        elif condition == 'reversal':
            # Exit reversal trades if trend continues in wrong direction
            # This would need trend analysis
            pass
        
        elif condition == 'breakout':
            # Exit breakout trades if price falls back into range
            # This would need support/resistance tracking
            pass
        
        elif condition == 'ranging':
            # Exit ranging trades at range boundaries
            # This would need range boundary detection
            pass
        
        return {'should_exit': False}
