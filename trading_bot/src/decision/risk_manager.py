"""
Risk Manager - Applies risk management rules to trade recommendations.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import math

from src.core.models import TradeRecommendation, MarketCondition
from src.utils.config import Config
from src.utils.logger import get_logger


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
        self._last_reset = datetime.utcnow().date()
    
    async def assess_risk(
        self, 
        recommendation: TradeRecommendation,
        current_price: Decimal,
        market_context: Any
    ) -> Dict[str, Any]:
        """Assess risk for a trade recommendation."""
        
        try:
            # Reset daily counters if needed
            self._reset_daily_counters()
            
            # Check basic risk rules
            basic_checks = self._check_basic_risk_rules(recommendation)
            if not basic_checks['approved']:
                return basic_checks
            
            # Check market condition specific rules
            condition_checks = self._check_market_condition_rules(recommendation, market_context)
            if not condition_checks['approved']:
                return condition_checks
            
            # Check position sizing
            sizing_checks = self._check_position_sizing(recommendation, current_price)
            if not sizing_checks['approved']:
                return sizing_checks
            
            # All checks passed
            return {
                'approved': True,
                'reason': 'Risk assessment passed',
                'notes': 'Trade meets all risk management criteria',
                'risk_score': self._calculate_risk_score(recommendation, market_context)
            }
            
        except Exception as e:
            self.logger.error(f"Error in risk assessment: {e}")
            return {
                'approved': False,
                'reason': f'Risk assessment error: {e}',
                'notes': 'Technical error in risk assessment'
            }
    
    def _check_basic_risk_rules(self, recommendation: TradeRecommendation) -> Dict[str, Any]:
        """Check basic risk management rules."""
        
        # Check confidence threshold
        if recommendation.confidence < self.config.ai_analysis.confidence_threshold:
            return {
                'approved': False,
                'reason': f'Confidence {recommendation.confidence:.2f} below threshold {self.config.ai_analysis.confidence_threshold}'
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
        
        # Check risk-reward ratio
        if recommendation.risk_reward_ratio < 1.5:
            return {
                'approved': False,
                'reason': f'Risk-reward ratio {recommendation.risk_reward_ratio:.2f} below minimum 1.5'
            }
        
        return {'approved': True, 'reason': 'Basic risk checks passed'}
    
    def _check_market_condition_rules(self, recommendation: TradeRecommendation, market_context: Any) -> Dict[str, Any]:
        """Check market condition specific risk rules."""
        
        condition = recommendation.market_condition
        
        if condition == MarketCondition.NEWS_REACTIONARY:
            # Higher risk in news-driven markets
            if recommendation.confidence < 0.8:
                return {
                    'approved': False,
                    'reason': 'News market requires higher confidence (0.8+)'
                }
            
            # Tighter stops for news markets
            if recommendation.estimated_hold_time > timedelta(hours=2):
                return {
                    'approved': False,
                    'reason': 'News market trades should be shorter duration'
                }
        
        elif condition == MarketCondition.REVERSAL:
            # Reversal trades need strong confirmation
            if recommendation.confidence < 0.75:
                return {
                    'approved': False,
                    'reason': 'Reversal trades require higher confidence (0.75+)'
                }
        
        elif condition == MarketCondition.BREAKOUT:
            # Breakout trades need volume confirmation
            if hasattr(market_context, 'volume') and market_context.volume < 1.5:
                return {
                    'approved': False,
                    'reason': 'Breakout requires volume confirmation'
                }
        
        elif condition == MarketCondition.RANGING:
            # Ranging markets need tight stops
            if recommendation.risk_reward_ratio > 3.0:
                return {
                    'approved': False,
                    'reason': 'Ranging market trades should have tighter stops'
                }
        
        return {'approved': True, 'reason': 'Market condition checks passed'}
    
    def _check_position_sizing(self, recommendation: TradeRecommendation, current_price: Decimal) -> Dict[str, Any]:
        """Check position sizing rules."""
        
        # Calculate potential loss
        if recommendation.stop_loss:
            potential_loss = abs(current_price - recommendation.stop_loss)
            loss_percentage = (potential_loss / current_price) * 100
            
            # Check if loss exceeds daily limit
            if self._daily_loss + potential_loss > self.max_daily_loss:
                return {
                    'approved': False,
                    'reason': f'Potential loss {potential_loss:.2f} would exceed daily limit'
                }
        
        return {'approved': True, 'reason': 'Position sizing checks passed'}
    
    async def calculate_position_size(
        self, 
        recommendation: TradeRecommendation, 
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate position size based on risk management rules."""
        
        try:
            # Get account balance (simulated for now)
            account_balance = Decimal('10000')  # $10,000 demo account
            
            # Calculate risk amount based on percentage
            risk_percentage = Decimal(str(self.config.trading.risk_percentage))
            risk_amount = account_balance * (risk_percentage / 100)
            
            # Calculate position size based on stop loss
            if recommendation.stop_loss and recommendation.entry_price:
                entry_price = Decimal(str(recommendation.entry_price))
                stop_loss = Decimal(str(recommendation.stop_loss))
                
                # Calculate pip value (simplified)
                pip_value = entry_price * Decimal('0.0001')  # For most pairs
                
                # Calculate position size
                risk_per_pip = abs(entry_price - stop_loss) / pip_value
                position_size = risk_amount / risk_per_pip
                
                # Apply maximum position size limit
                max_size = self.max_position_size
                position_size = min(position_size, max_size)
                
                return {
                    'size': position_size,
                    'risk_amount': risk_amount,
                    'stop_loss': stop_loss,
                    'take_profit': recommendation.take_profit
                }
            
            else:
                # Fallback calculation
                position_size = account_balance * Decimal('0.01')  # 1% of account
                return {
                    'size': position_size,
                    'risk_amount': risk_amount,
                    'stop_loss': recommendation.stop_loss,
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
        today = datetime.utcnow().date()
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