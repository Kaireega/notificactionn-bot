"""
Improved Risk Manager - Enhanced risk management with unified data sources and fundamental analysis integration.
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


class ImprovedRiskManager:
    """Enhanced risk management with unified data sources and fundamental analysis integration."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Risk parameters
        self.max_daily_loss = Decimal(str(config.risk_management.max_daily_loss))
        self.max_position_size = Decimal(str(config.risk_management.max_position_size))
        self.correlation_limit = config.risk_management.correlation_limit
        
        # Debug logging for position sizing
        self.logger.info(f"Risk Manager initialized with max_position_size: {self.max_position_size}")
        self.logger.info(f"Config risk_management.max_position_size: {config.risk_management.max_position_size}")
        self.max_open_trades = config.risk_management.max_open_trades
        self.stop_loss_atr_multiplier = config.risk_management.stop_loss_atr_multiplier
        self.trailing_stop = config.risk_management.trailing_stop
        self.trailing_stop_atr_multiplier = config.risk_management.trailing_stop_atr_multiplier
        
        # Unified data source for all risk checks
        self._shared_risk_data = {
            'daily_trades': 0,
            'open_positions': {},
            'daily_loss': Decimal('0'),
            'account_balance': Decimal(str(getattr(config, 'account_balance', 100000))),
            'last_reset': datetime.now().date(),
            'fundamental_scores': {},
            'market_conditions': {},
            'correlation_data': {}
        }
        
        # Enhanced confidence thresholds - Stricter requirements
        self.confidence_thresholds = {
            'minimum': 0.7,      # Increased minimum confidence for any trade
            'low': 0.75,         # Low confidence trades
            'medium': 0.8,       # Medium confidence trades
            'high': 0.85,        # High confidence trades
            'excellent': 0.9     # Excellent confidence trades
        }
        
        # Enhanced entry criteria thresholds
        self.entry_criteria = {
            'minimum_signal_strength': 0.6,
            'minimum_consensus_score': 0.8,
            'minimum_risk_reward': 2.0,
            'minimum_rsi_divergence': 0.3,
            'minimum_macd_signal': 0.0002,
            'bollinger_threshold': 0.05,
            'volume_spike_threshold': 1.5
        }
        
        # Market condition risk scores
        self.market_condition_risk_scores = {
            MarketCondition.NEWS_REACTIONARY: 0.2,  # Highest risk
            MarketCondition.REVERSAL: 0.4,          # High risk
            MarketCondition.BREAKOUT: 0.6,          # Medium risk
            MarketCondition.RANGING: 0.8,           # Low risk
            MarketCondition.UNKNOWN: 0.5            # Medium risk
        }
        
        # Currency pip locations for position sizing
        self.pip_locations = {
            'JPY_PAIRS': ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY', 'CAD_JPY', 'CHF_JPY'],
            'STANDARD_PAIRS': ['EUR_USD', 'GBP_USD', 'AUD_USD', 'NZD_USD', 'USD_CAD', 'USD_CHF', 'EUR_GBP', 'EUR_AUD', 'GBP_AUD']
        }
    
    async def assess_risk(self, recommendation: TradeRecommendation, current_price: float, 
                         market_context: MarketContext, fundamental_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced risk assessment with fundamental analysis integration."""
        try:
            # Convert current_price to Decimal for consistency
            current_price_decimal = Decimal(str(current_price))
            
            # Update shared data
            self._update_shared_data(recommendation.pair, fundamental_analysis, market_context)
            
            # Basic risk checks (30% weight)
            basic_checks = self._check_enhanced_basic_risk_rules(recommendation)
            self.logger.debug(f"Basic risk checks for {recommendation.pair}: {basic_checks}")
            if not basic_checks['approved']:
                return {
                    'approved': False,
                    'reason': basic_checks['reason'],
                    'risk_score': 1.0
                }
            
            # Market condition checks (25% weight)
            condition_checks = self._check_enhanced_market_condition_rules(recommendation, market_context)
            self.logger.debug(f"Market condition checks for {recommendation.pair}: {condition_checks}")
            if not condition_checks['approved']:
                return {
                    'approved': False,
                    'reason': condition_checks['reason'],
                    'risk_score': 0.8
                }
            
            # Position sizing checks (25% weight)
            sizing_checks = self._check_enhanced_position_sizing(recommendation, current_price_decimal)
            self.logger.debug(f"Position sizing checks for {recommendation.pair}: {sizing_checks}")
            if not sizing_checks['approved']:
                return {
                    'approved': False,
                    'reason': sizing_checks['reason'],
                    'risk_score': 0.6
                }
            
            # Fundamental analysis checks (20% weight)
            fundamental_checks = await self._check_fundamental_conditions(recommendation, fundamental_analysis)
            self.logger.debug(f"Fundamental checks for {recommendation.pair}: {fundamental_checks}")
            if not fundamental_checks['approved']:
                return {
                    'approved': False,
                    'reason': fundamental_checks['reason'],
                    'risk_score': 0.7
                }
            
            # Calculate weighted risk score
            basic_score = basic_checks.get('score', 0.5) * 0.3
            condition_score = condition_checks.get('score', 0.5) * 0.25
            sizing_score = sizing_checks.get('score', 0.5) * 0.25
            fundamental_score = fundamental_checks.get('score', 0.5) * 0.2
            
            risk_score = basic_score + condition_score + sizing_score + fundamental_score
            
            # Enhanced approval threshold: risk_score must be < 0.7 for approval
            approved = risk_score < 0.7
            
            result = {
                'approved': approved,
                'reason': 'Enhanced risk assessment completed',
                'risk_score': risk_score,
                'max_position_size': sizing_checks.get('max_size', 0.0),
                'fundamental_score': fundamental_score,
                'confidence_score': basic_checks.get('confidence_score', 0.0),
                'market_condition_score': condition_score,
                'position_sizing_score': sizing_score
            }
            
            self.logger.debug(f"Final risk assessment for {recommendation.pair}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced risk assessment: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'approved': False,
                'reason': f'Enhanced risk assessment error: {str(e)}',
                'risk_score': 1.0
            }
    
    def _update_shared_data(self, pair: str, fundamental_analysis: Optional[Dict], market_context: MarketContext):
        """Update shared risk data."""
        if fundamental_analysis:
            self._shared_risk_data['fundamental_scores'][pair] = fundamental_analysis.get('fundamental_score', 0.5)
        
        if market_context and hasattr(market_context, 'condition'):
            self._shared_risk_data['market_conditions'][pair] = market_context.condition
        else:
            # Default to UNKNOWN if market_context is None or missing condition
            from ..core.models import MarketCondition
            self._shared_risk_data['market_conditions'][pair] = MarketCondition.UNKNOWN
        
        # Reset daily counters if it's a new day
        self._reset_daily_counters()
    
    def _check_enhanced_basic_risk_rules(self, recommendation: TradeRecommendation) -> Dict[str, Any]:
        """Enhanced basic risk management rules with better confidence scoring."""
        
        # Enhanced confidence scoring
        confidence = recommendation.confidence
        if confidence < self.confidence_thresholds['minimum']:
            confidence_score = 0.0
        elif confidence < self.confidence_thresholds['low']:
            confidence_score = 0.25
        elif confidence < self.confidence_thresholds['medium']:
            confidence_score = 0.5
        elif confidence < self.confidence_thresholds['high']:
            confidence_score = 0.75
        elif confidence < self.confidence_thresholds['excellent']:
            confidence_score = 0.9
        else:
            confidence_score = 1.0
        
        if confidence < self.confidence_thresholds['minimum']:
            return {
                'approved': False,
                'reason': f'Confidence {confidence:.2f} below minimum threshold {self.confidence_thresholds["minimum"]}',
                'score': confidence_score,
                'confidence_score': confidence_score
            }
        
        # Check daily trade limit using shared data
        daily_trades = self._shared_risk_data['daily_trades']
        if daily_trades >= self.config.trading.max_trades_per_day:
            return {
                'approved': False,
                'reason': f'Daily trade limit reached ({daily_trades}/{self.config.trading.max_trades_per_day})',
                'score': 0.0,
                'confidence_score': confidence_score
            }
        
        # Check open positions limit using shared data
        open_positions = self._shared_risk_data['open_positions']
        self.logger.debug(f"Open positions check for {recommendation.pair}: {len(open_positions)}/{self.max_open_trades}")
        
        # Debug open positions if we're at the limit
        if len(open_positions) >= self.max_open_trades:
            self.debug_open_positions()
            return {
                'approved': False,
                'reason': f'Maximum open trades reached ({len(open_positions)}/{self.max_open_trades})',
                'score': 0.0,
                'confidence_score': confidence_score
            }
        
        # Enhanced risk-reward ratio check - Stricter requirement
        if recommendation.risk_reward_ratio < self.entry_criteria['minimum_risk_reward']:
            return {
                'approved': False,
                'reason': f'Risk-reward ratio {recommendation.risk_reward_ratio:.2f} below minimum {self.entry_criteria["minimum_risk_reward"]}',
                'score': 0.3,
                'confidence_score': confidence_score
            }
        
        # Enhanced signal strength check
        if hasattr(recommendation, 'signal_strength') and recommendation.signal_strength < self.entry_criteria['minimum_signal_strength']:
            return {
                'approved': False,
                'reason': f'Signal strength {recommendation.signal_strength:.2f} below minimum {self.entry_criteria["minimum_signal_strength"]}',
                'score': 0.4,
                'confidence_score': confidence_score
            }
        
        # Calculate overall basic score with enhanced weighting
        rr_score = min(recommendation.risk_reward_ratio / 4.0, 1.0)  # Normalize to 0-1 with higher target
        signal_score = getattr(recommendation, 'signal_strength', 0.5) / self.entry_criteria['minimum_signal_strength']
        signal_score = min(signal_score, 1.0)
        
        basic_score = (confidence_score * 0.5) + (rr_score * 0.3) + (signal_score * 0.2)
        
        return {
            'approved': True, 
            'reason': 'Enhanced basic risk checks passed', 
            'score': basic_score,
            'confidence_score': confidence_score
        }
    
    def _check_enhanced_market_condition_rules(self, recommendation: TradeRecommendation, market_context: MarketContext) -> Dict[str, Any]:
        """Enhanced market condition specific risk rules."""
        
        condition = recommendation.market_condition
        base_score = self.market_condition_risk_scores.get(condition, 0.5)
        
        # Enhanced market condition checks with stricter requirements
        if condition == MarketCondition.NEWS_REACTIONARY:
            # Higher risk in news-driven markets - require 80% confidence
            if recommendation.confidence < 0.8:
                return {
                    'approved': False,
                    'reason': f'News reactionary markets require 80%+ confidence (current: {recommendation.confidence:.2f})',
                    'score': 0.2
                }
            # Require higher risk/reward for news trades
            if recommendation.risk_reward_ratio < 2.5:
                return {
                    'approved': False,
                    'reason': f'News trades require R/R ratio >= 2.5 (current: {recommendation.risk_reward_ratio:.2f})',
                    'score': 0.3
                }
        
        elif condition == MarketCondition.REVERSAL:
            # Reversal trades need strong confirmation - require 75% confidence
            if recommendation.confidence < 0.75:
                return {
                    'approved': False,
                    'reason': f'Reversal trades require 75%+ confidence (current: {recommendation.confidence:.2f})',
                    'score': 0.3
                }
            # Require higher risk/reward for reversal trades
            if recommendation.risk_reward_ratio < 2.0:
                return {
                    'approved': False,
                    'reason': f'Reversal trades require R/R ratio >= 2.0 (current: {recommendation.risk_reward_ratio:.2f})',
                    'score': 0.4
                }
        
        elif condition == MarketCondition.BREAKOUT:
            # Breakout trades need good confirmation - require 70% confidence
            if recommendation.confidence < 0.7:
                return {
                    'approved': False,
                    'reason': f'Breakout trades require 70%+ confidence (current: {recommendation.confidence:.2f})',
                    'score': 0.4
                }
            # Require volume confirmation for breakouts
            if hasattr(recommendation, 'volume_confirmed') and not recommendation.volume_confirmed:
                return {
                    'approved': False,
                    'reason': 'Breakout trades require volume confirmation',
                    'score': 0.5
                }
        
        elif condition == MarketCondition.RANGING:
            # Ranging trades need high confidence - require 80% confidence
            if recommendation.confidence < 0.8:
                return {
                    'approved': False,
                    'reason': f'Ranging trades require 80%+ confidence (current: {recommendation.confidence:.2f})',
                    'score': 0.3
                }
            # Lower risk/reward acceptable for ranging trades
            if recommendation.risk_reward_ratio > 1.5:
                return {
                    'approved': False,
                    'reason': f'Ranging trades should have R/R ratio <= 1.5 (current: {recommendation.risk_reward_ratio:.2f})',
                    'score': 0.4
                }
        

        
        return {
            'approved': True, 
            'reason': 'Enhanced market condition checks passed', 
            'score': base_score
        }
    
    def _check_enhanced_position_sizing(self, recommendation: TradeRecommendation, current_price: Decimal) -> Dict[str, Any]:
        """Enhanced position sizing checks with currency-specific calculations."""
        
        # Calculate potential loss with currency-specific pip values
        if recommendation.stop_loss and current_price > 0:
            pip_size = self._get_pip_size(recommendation.pair)
            potential_loss_pips = abs(float(current_price - recommendation.stop_loss)) / pip_size
            pip_value = self._calculate_pip_value(recommendation.pair, current_price, pip_size)
            # Convert both to Decimal for consistent calculation
            potential_loss_dollars = Decimal(str(potential_loss_pips)) * pip_value
            
            # Check if loss exceeds daily limit
            if self._shared_risk_data['daily_loss'] + potential_loss_dollars > self.max_daily_loss:
                return {
                    'approved': False,
                    'reason': f'Potential loss ${potential_loss_dollars:.2f} would exceed daily limit ${self.max_daily_loss}',
                    'score': 0.2
                }
        
        return {
            'approved': True, 
            'reason': 'Enhanced position sizing checks passed', 
            'score': 0.7,
            'max_size': float(self.max_position_size)
        }
    
    async def _check_fundamental_conditions(self, recommendation: TradeRecommendation, fundamental_analysis: Optional[Dict]) -> Dict[str, Any]:
        """Check fundamental analysis conditions."""
        
        if not fundamental_analysis:
            return {
                'approved': True,
                'reason': 'No fundamental analysis available',
                'score': 0.5
            }
        
        fundamental_score = fundamental_analysis.get('fundamental_score', 0.5)
        avoid_trading = fundamental_analysis.get('avoid_trading', False)
        
        if avoid_trading:
            return {
                'approved': False,
                'reason': 'Fundamental analysis suggests avoiding trading',
                'score': 0.1
            }
        
        # Score based on fundamental analysis
        if fundamental_score >= 0.8:
            score = 0.9
        elif fundamental_score >= 0.6:
            score = 0.7
        elif fundamental_score >= 0.4:
            score = 0.5
        else:
            score = 0.3
        
        return {
            'approved': True,
            'reason': f'Fundamental analysis passed (score: {fundamental_score:.2f})',
            'score': score
        }
    
    async def calculate_position_size(
        self, 
        recommendation: TradeRecommendation, 
        risk_assessment: Dict[str, Any],
        fundamental_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Enhanced FX position size calculation with currency decimals and fundamental multiplier."""
        
        try:
            if not (recommendation.stop_loss and recommendation.entry_price):
                return {
                    'size': Decimal('0'),
                    'risk_amount': Decimal('0'),
                    'stop_loss': recommendation.stop_loss,
                    'take_profit': recommendation.take_profit
                }

            # Account balance and risk percent
            account_balance = self._shared_risk_data['account_balance']
            risk_percentage = Decimal(str(self.config.trading.risk_percentage))
            risk_amount = account_balance * (risk_percentage / 100)
            
            pair = recommendation.pair
            self.logger.info(f"Risk calculation for {pair}: Account=${account_balance}, Risk%={risk_percentage}%, RiskAmount=${risk_amount}")
            entry_price = Decimal(str(recommendation.entry_price))
            stop_loss = Decimal(str(recommendation.stop_loss))

            # Get pip location and size for currency pair
            pip_location = self._get_pip_location(pair)
            pip_size = self._get_pip_size(pair)
            
            # Calculate position size based on stop loss distance
            stop_loss_distance = abs(entry_price - stop_loss)
            if stop_loss_distance > 0:
                # Calculate how many pips the stop loss is
                pips_to_stop_loss = stop_loss_distance / Decimal(str(pip_size))
                
                # Calculate position size: Risk Amount / (Pips to Stop Loss × Pip Value)
                # For a standard lot (100,000 units), 1 pip = $10
                standard_lot_pip_value = Decimal('10')
                units = (risk_amount * Decimal('100000')) / (pips_to_stop_loss * standard_lot_pip_value)
                
                self.logger.info(f"Position sizing for {pair}: Account=${account_balance}, Risk=${risk_amount}, StopLoss={pips_to_stop_loss} pips, Units={units}")
            else:
                units = 0
                self.logger.warning(f"Zero stop loss distance for {pair}")

            # Apply fundamental multiplier if available
            if fundamental_analysis:
                fundamental_multiplier = fundamental_analysis.get('position_size_multiplier', 1.0)
                units = units * Decimal(str(fundamental_multiplier))
                self.logger.info(f"Applied fundamental multiplier: {fundamental_multiplier:.3f}")

            # Respect maximum size
            max_size = Decimal(str(self.max_position_size))
            self.logger.info(f"Position sizing check for {pair}: calculated units={units}, max_size={max_size}")
            units = min(units, max_size)
            self.logger.info(f"Final position size for {pair}: {units} units (max: {max_size})")

            return {
                'size': Decimal(str(units)),
                'risk_amount': risk_amount,
                'stop_loss': stop_loss,
                'take_profit': recommendation.take_profit,
                'pip_location': pip_location,
                'pip_size': pip_size,
                'pip_value': Decimal('0.0001'),  # Fixed pip value for return
                'fundamental_multiplier': fundamental_analysis.get('position_size_multiplier', 1.0) if fundamental_analysis else 1.0
            }
                
        except Exception as e:
            self.logger.error(f"Error calculating enhanced position size: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'size': Decimal('0.01'),
                'risk_amount': Decimal('100'),
                'stop_loss': recommendation.stop_loss,
                'take_profit': recommendation.take_profit
            }
    
    def _get_pip_location(self, pair: str) -> int:
        """Get pip location for currency pair."""
        # JPY pairs have 2 decimal places, others have 4
        if any(jpy_pair in pair for jpy_pair in self.pip_locations['JPY_PAIRS']):
            return -2
        else:
            return -4
    
    def _get_pip_size(self, pair: str) -> float:
        """Get pip size for currency pair."""
        if any(jpy_pair in pair for jpy_pair in self.pip_locations['JPY_PAIRS']):
            return 0.01  # JPY pairs
        else:
            return 0.0001  # Standard pairs
    
    def _calculate_pip_value(self, pair: str, entry_price: Decimal, pip_size: float) -> Decimal:
        """Calculate pip value for position sizing."""
        # Calculate actual pip value based on position size
        # For a standard lot (100,000 units), 1 pip = $10 for most pairs
        # For JPY pairs, 1 pip = $10 for 100,000 units
        
        # Standard lot size
        standard_lot = Decimal('100000')
        
        # Calculate pip value per unit
        if pip_size == 0.01:  # JPY pairs
            # For JPY pairs, 1 pip = $10 for 100,000 units
            pip_value_per_unit = Decimal('10') / standard_lot
        else:  # Other pairs (EUR/USD, GBP/USD, etc.)
            # For other pairs, 1 pip = $10 for 100,000 units
            pip_value_per_unit = Decimal('10') / standard_lot
        
        # For position sizing, we need the dollar value per pip for the risk amount
        # This should be calculated based on the stop loss distance
        return pip_value_per_unit
    
    def _reset_daily_counters(self) -> None:
        """Reset daily counters if it's a new day."""
        today = datetime.now().date()
        if today > self._shared_risk_data['last_reset']:
            self._shared_risk_data['daily_loss'] = Decimal('0')
            self._shared_risk_data['daily_trades'] = 0
            self._shared_risk_data['last_reset'] = today
    
    def update_trade_result(self, pair: str, profit_loss: Decimal) -> None:
        """Update risk manager with trade result."""
        self._shared_risk_data['daily_loss'] += profit_loss
        if pair in self._shared_risk_data['open_positions']:
            del self._shared_risk_data['open_positions'][pair]
    
    def add_open_position(self, pair: str, trade_data: Dict[str, Any]) -> None:
        """Add an open position to tracking."""
        current_count = len(self._shared_risk_data['open_positions'])
        if current_count >= self.max_open_trades:
            self.logger.warning(f"Cannot add position for {pair}: Max open trades reached ({current_count}/{self.max_open_trades})")
            return False
        
        self._shared_risk_data['open_positions'][pair] = trade_data
        self._shared_risk_data['daily_trades'] += 1
        self.logger.info(f"Added open position for {pair}. Total open positions: {len(self._shared_risk_data['open_positions'])}")
        return True
    
    def sync_open_positions(self, actual_open_positions: Dict[str, Any]) -> None:
        """Sync risk manager with actual open positions from position manager."""
        self._shared_risk_data['open_positions'] = actual_open_positions.copy()
        self.logger.info(f"Synced open positions: {list(actual_open_positions.keys())}. Total: {len(actual_open_positions)}")
    
    def clear_open_positions(self) -> None:
        """Clear all open positions (for testing/reset)."""
        self._shared_risk_data['open_positions'] = {}
        self.logger.info("Cleared all open positions")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        return {
            'daily_trades': self._shared_risk_data['daily_trades'],
            'open_positions': len(self._shared_risk_data['open_positions']),
            'daily_loss': float(self._shared_risk_data['daily_loss']),
            'account_balance': float(self._shared_risk_data['account_balance']),
            'max_daily_loss': float(self.max_daily_loss),
            'max_open_trades': self.max_open_trades,
            'fundamental_scores': self._shared_risk_data['fundamental_scores'],
            'market_conditions': {k: v.value for k, v in self._shared_risk_data['market_conditions'].items()}
        }
    
    def debug_open_positions(self) -> None:
        """Debug method to print current open positions."""
        self.logger.info(f"🔍 Risk Manager Open Positions Debug:")
        self.logger.info(f"   Max Open Trades: {self.max_open_trades}")
        self.logger.info(f"   Current Open Positions: {len(self._shared_risk_data['open_positions'])}")
        self.logger.info(f"   Open Position Pairs: {list(self._shared_risk_data['open_positions'].keys())}")
        for pair, data in self._shared_risk_data['open_positions'].items():
            self.logger.info(f"   - {pair}: {data}")
