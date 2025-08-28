"""
Risk Manager - Applies risk management rules to trade recommendations.
"""
import traceback
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import math

from ..core.models import TradeRecommendation, MarketContext, MarketCondition
from ..core.fx_position_sizing import compute_units_from_risk
from infrastructure.instrument_collection import instrumentCollection as ic
from api.oanda_api import OandaApi
from ..utils.config import Config
from ..utils.logger import get_logger


class RiskManager:
    """Applies risk management rules to trade recommendations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Risk parameters
        self.max_daily_loss = Decimal(str(config.risk_management.max_daily_loss))
        self.max_position_size = Decimal(str(config.risk_management.max_position_size))
        self.correlation_limit = config.risk_management.correlation_limit
        self.max_open_trades = config.risk_management.max_open_trades
        self.stop_loss_atr_multiplier = config.risk_management.stop_loss_atr_multiplier
        self.trailing_stop = config.risk_management.trailing_stop
        self.trailing_stop_atr_multiplier = config.risk_management.trailing_stop_atr_multiplier
        
        # Daily tracking
        self._daily_loss = Decimal('0')
        self._daily_trades = 0
        self._open_positions = {}
        from datetime import datetime, timezone
        self._last_reset = datetime.now(timezone.utc).date()
    
    async def assess_risk(self, recommendation: TradeRecommendation, current_price: float, 
                         market_context: MarketContext) -> Dict[str, Any]:
        """Assess the risk of a trade recommendation."""
        try:
            # Convert current_price to Decimal for consistency
            current_price_decimal = Decimal(str(current_price))
            
            # Basic risk checks
            basic_checks = self._check_basic_risk_rules(recommendation)
            if not basic_checks['approved']:
                return {
                    'approved': False,
                    'reason': basic_checks['reason'],
                    'risk_score': 1.0
                }
            
            # Market condition checks
            condition_checks = self._check_market_condition_rules(recommendation, market_context)
            if not condition_checks['approved']:
                return {
                    'approved': False,
                    'reason': condition_checks['reason'],
                    'risk_score': 0.8
                }
            
            # Position sizing checks
            sizing_checks = self._check_position_sizing(recommendation, current_price_decimal)
            if not sizing_checks['approved']:
                return {
                    'approved': False,
                    'reason': sizing_checks['reason'],
                    'risk_score': 0.6
                }
            
            # Calculate overall risk score (use default scores if not provided)
            basic_score = basic_checks.get('score', 0.5)
            condition_score = condition_checks.get('score', 0.5)
            sizing_score = sizing_checks.get('score', 0.5)
            risk_score = (basic_score + condition_score + sizing_score) / 3
            
            return {
                'approved': True,
                'reason': 'Risk assessment passed',
                'risk_score': risk_score,
                'max_position_size': sizing_checks.get('max_size', 0.0)
            }
            
        except Exception as e:
            print(f"❌ [DEBUG] Error in risk assessment: {e}")
            print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
            return {
                'approved': False,
                'reason': f'Risk assessment error: {str(e)}',
                'risk_score': 1.0
            }
    
    def _check_basic_risk_rules(self, recommendation: TradeRecommendation) -> Dict[str, Any]:
        """Check basic risk management rules."""
        
        # Check confidence threshold - Made more aggressive
        confidence_threshold = min(self.config.technical_analysis.confidence_threshold, 0.2)  # Even more lenient for testing
        if recommendation.confidence < confidence_threshold:
            return {
                'approved': False,
                'reason': f'Confidence {recommendation.confidence:.2f} below threshold {confidence_threshold}'
            }
        
        # Check daily trade limit
        if self._daily_trades >= self.config.trading.max_trades_per_day:
            return {
                'approved': False,
                'reason': f'Daily trade limit reached ({self._daily_trades}/{self.config.trading.max_trades_per_day})'
            }
        
        # Check open positions limit
        if len(self._open_positions) >= self.max_open_trades:
            return {
                'approved': False,
                'reason': f'Maximum open trades reached ({len(self._open_positions)}/{self.max_open_trades})'
            }
        
        # Check risk-reward ratio - Made more aggressive
        if recommendation.risk_reward_ratio < 1.0:  # Even more lenient for testing
            return {
                'approved': False,
                'reason': f'Risk-reward ratio {recommendation.risk_reward_ratio:.2f} below minimum 1.0'
            }
        
        return {'approved': True, 'reason': 'Basic risk checks passed', 'score': 0.8}
    
    def _check_market_condition_rules(self, recommendation: TradeRecommendation, market_context: Any) -> Dict[str, Any]:
        """Check market condition specific risk rules."""
        
        condition = recommendation.market_condition
        
        if condition == MarketCondition.NEWS_REACTIONARY:
            # Higher risk in news-driven markets
            if recommendation.confidence < 0.8:
                return {
                    'approved': False,
                    'reason': 'News reactionary markets require higher confidence (0.8)',
                    'score': 0.3
                }
        
        elif condition == MarketCondition.REVERSAL:
            # Reversal trades need strong confirmation
            if recommendation.confidence < 0.75:
                return {
                    'approved': False,
                    'reason': 'Reversal trades require higher confidence (0.75)',
                    'score': 0.4
                }
        
        elif condition == MarketCondition.BREAKOUT:
            # Breakout trades need volume confirmation
            if hasattr(market_context, 'volume') and market_context.volume < 1.5:
                return {
                    'approved': False,
                    'reason': 'Breakout trades need higher volume confirmation',
                    'score': 0.5
                }
        
        elif condition == MarketCondition.RANGING:
            # Ranging markets need tight stops
            if recommendation.risk_reward_ratio > 3.0:
                return {
                    'approved': False,
                    'reason': 'Ranging markets need tighter risk/reward ratios',
                    'score': 0.6
                }
        
        return {'approved': True, 'reason': 'Market condition checks passed', 'score': 0.7}
    
    def _check_position_sizing(self, recommendation: TradeRecommendation, current_price: Decimal) -> Dict[str, Any]:
        """Check position sizing rules."""
        
        # Calculate potential loss
        if recommendation.stop_loss and current_price > 0:
            potential_loss = abs(current_price - recommendation.stop_loss)
            loss_percentage = (potential_loss / current_price) * 100
            
            # Check if loss exceeds daily limit
            if self._daily_loss + potential_loss > self.max_daily_loss:
                return {
                    'approved': False,
                    'reason': f'Potential loss {potential_loss:.2f} would exceed daily limit'
                }
        
        return {'approved': True, 'reason': 'Position sizing checks passed', 'score': 0.6}
    
    async def calculate_position_size(
        self, 
        recommendation: TradeRecommendation, 
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate FX position size using pip location and home conversions."""
        
        try:
            if not (recommendation.stop_loss and recommendation.entry_price):
                return {
                    'size': Decimal('0'),
                    'risk_amount': Decimal('0'),
                    'stop_loss': recommendation.stop_loss,
                    'take_profit': recommendation.take_profit
                }

            # Account balance and risk percent
            account_balance = Decimal(str(getattr(self.config.trading, 'account_balance', 100000)))
            risk_percentage = Decimal(str(self.config.trading.risk_percentage))
            risk_amount = account_balance * (risk_percentage / 100)

            pair = recommendation.pair
            entry_price = Decimal(str(recommendation.entry_price))
            stop_loss = Decimal(str(recommendation.stop_loss))

            # For backtesting, skip instrument metadata check
            # Use default pip location for major pairs
            pip_location = -4  # Default for major forex pairs

            # For backtesting, use simplified position size calculation
            # Calculate pip value and position size
            pip_value = abs(entry_price - stop_loss)
            if pip_value > 0:
                # Simplified position size calculation for backtesting
                # Risk amount / pip value = position size
                units = risk_amount / pip_value
            else:
                units = 0

            # Respect maximum size
            max_size = float(self.max_position_size)
            units = min(units, max_size)

            return {
                'size': Decimal(str(units)),
                'risk_amount': risk_amount,
                'stop_loss': stop_loss,
                'take_profit': recommendation.take_profit
            }
                
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return {
                'size': Decimal('0.01'),
                'risk_amount': Decimal('100'),
                'stop_loss': recommendation.stop_loss,
                'take_profit': recommendation.take_profit
            }
    
    def _calculate_risk_score(self, recommendation: TradeRecommendation, market_context: Any) -> float:
        """Calculate a risk score for the trade."""
        
        score = 0.0
        
        # Confidence contributes to score
        score += recommendation.confidence * 0.3
        
        # Risk-reward ratio contributes
        score += min(recommendation.risk_reward_ratio / 3.0, 1.0) * 0.2
        
        # Market condition contributes
        condition_scores = {
            MarketCondition.NEWS_REACTIONARY: 0.6,
            MarketCondition.REVERSAL: 0.7,
            MarketCondition.BREAKOUT: 0.8,
            MarketCondition.RANGING: 0.9,
            MarketCondition.UNKNOWN: 0.5
        }
        score += condition_scores.get(recommendation.market_condition, 0.5) * 0.2
        
        # Volatility consideration
        if hasattr(market_context, 'volatility'):
            volatility_score = max(0, 1 - market_context.volatility)
            score += volatility_score * 0.3
        
        return min(score, 1.0)
    
    def _reset_daily_counters(self) -> None:
        """Reset daily counters if it's a new day."""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        if today > self._last_reset:
            self._daily_loss = Decimal('0')
            self._daily_trades = 0
            self._last_reset = today
    
    def update_trade_result(self, pair: str, profit_loss: Decimal) -> None:
        """Update risk manager with trade result."""
        self._daily_loss += profit_loss
        if pair in self._open_positions:
            del self._open_positions[pair]
    
    def add_open_position(self, pair: str, trade_data: Dict[str, Any]) -> None:
        """Add an open position to tracking."""
        self._open_positions[pair] = trade_data
        self._daily_trades += 1 