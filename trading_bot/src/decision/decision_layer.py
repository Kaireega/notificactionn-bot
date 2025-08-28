"""
Decision Layer - Applies risk management and validates trade recommendations.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json

from ..core.models import (
    TradeRecommendation, TradeDecision, MarketCondition, TradeSignal,
    PerformanceMetrics, CandleData, TimeFrame, TechnicalIndicators, MarketContext
)
from ..utils.config import Config
from ..utils.logger import get_logger
from .risk_manager import RiskManager
from .performance_tracker import PerformanceTracker
from .enhanced_excel_trade_recorder import EnhancedExcelTradeRecorder


class DecisionLayer:
    """Applies risk management and makes final trade decisions."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.risk_manager = RiskManager(config)
        self.performance_tracker = PerformanceTracker()
        self.trade_recorder = EnhancedExcelTradeRecorder(config)
        
        # Decision tracking
        self._daily_trades: List[TradeDecision] = []
        self._open_positions: Dict[str, TradeDecision] = {}
        self._last_decision_time: Dict[str, datetime] = {}
        
        # Performance metrics
        self._performance_metrics = PerformanceMetrics()
    
    async def process_recommendation(
        self, 
        recommendation: TradeRecommendation,
        current_price: Decimal,
        market_context: Any,
        technical_indicators: Dict[TimeFrame, TechnicalIndicators] = None,
        candles_by_timeframe: Dict[TimeFrame, List[CandleData]] = None,
        ai_outputs: Dict[str, Any] = None,
        multi_timeframe_analysis: Dict[str, Any] = None,
        risk_assessment: Dict[str, Any] = None,
        raw_data: Dict[str, Any] = None
    ) -> Optional[TradeDecision]:
        """Process AI recommendation and apply risk management."""
        
        try:
            # Check if we should process this recommendation
            if not self._should_process_recommendation(recommendation):
                self.logger.info(
                    f"🚫 Skipping recommendation for {recommendation.pair}: "
                    f"confidence {recommendation.confidence:.2f} below threshold "
                    f"({self.config.technical_analysis.confidence_threshold})"
                )
                return None
            
            # Apply risk management rules
            risk_assessment = await self.risk_manager.assess_risk(
                recommendation, current_price, market_context
            )
            
            if not risk_assessment['approved']:
                self.logger.info(f"⚠️ Risk management rejected trade for {recommendation.pair}: "
                               f"{risk_assessment['reason']}")
                return self._create_rejected_decision(recommendation, risk_assessment)
            
            # Calculate position size and risk parameters
            position_size = await self.risk_manager.calculate_position_size(
                recommendation, risk_assessment
            )
            
            # Create trade decision
            decision = TradeDecision(
                recommendation=recommendation,
                approved=True,
                position_size=position_size['size'],
                risk_amount=position_size['risk_amount'],
                modified_stop_loss=position_size['stop_loss'],
                modified_take_profit=position_size['take_profit'],
                risk_management_notes=risk_assessment['notes'],
                timestamp=datetime.now(timezone.utc)
            )
            
            # Log successful decision
            self.logger.info(f"✅ Trade APPROVED for {recommendation.pair}: "
                           f"Signal={recommendation.signal}, "
                           f"Size={position_size['size']:.2f}, "
                           f"Risk=${position_size['risk_amount']:.2f}")
            
            # Log decision
            self._log_decision(decision)
            
            # Record the COMPLETE trade decision with ALL data
            if self.trade_recorder:
                self.trade_recorder.record_complete_trade_decision(
                    decision=decision,
                    market_context=market_context,
                    technical_indicators=technical_indicators or {},
                    candles_by_timeframe=candles_by_timeframe or {},
                    ai_outputs=ai_outputs or {},
                    multi_timeframe_analysis=multi_timeframe_analysis or {},
                    risk_assessment=risk_assessment or {},
                    raw_data=raw_data or {}
                )
            
            # Update tracking
            self._daily_trades.append(decision)
            self._last_decision_time[recommendation.pair] = datetime.now(timezone.utc)
            
            self.logger.info(f"Approved trade decision for {recommendation.pair}: "
                           f"{recommendation.signal.value} at {current_price}")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error processing recommendation for {recommendation.pair}: {e}")
            return None
    
    def _should_process_recommendation(self, recommendation: TradeRecommendation) -> bool:
        """Check if recommendation meets basic criteria for processing."""
        
        # Check confidence threshold
        if recommendation.confidence < self.config.technical_analysis.confidence_threshold:
            self.logger.debug(f"🔍 Confidence check failed for {recommendation.pair}: "
                            f"{recommendation.confidence:.2f} < {self.config.technical_analysis.confidence_threshold}")
            return False
        
        # Check if we already have a recent decision for this pair
        if recommendation.pair in self._last_decision_time:
            from datetime import datetime, timezone
            time_since_last = datetime.now(timezone.utc) - self._last_decision_time[recommendation.pair]
            if time_since_last.total_seconds() < self.config.min_decision_interval:
                self.logger.debug(f"🔍 Rate limit check failed for {recommendation.pair}: "
                                f"{time_since_last.total_seconds():.1f}s < {self.config.min_decision_interval}s")
                return False
        
        # Check daily trade limit
        today_trades = [t for t in self._daily_trades 
                       if t.timestamp.date() == datetime.now(timezone.utc).date()]
        if len(today_trades) >= self.config.max_trades_per_day:
            self.logger.warning(f"🔍 Daily trade limit reached for {recommendation.pair}: "
                              f"{len(today_trades)} >= {self.config.max_trades_per_day}")
            return False
        
        # Check if we have an open position for this pair
        if recommendation.pair in self._open_positions:
            self.logger.debug(f"🔍 Open position check failed for {recommendation.pair}: "
                            f"Already have open position")
            return False
        
        self.logger.debug(f"✅ All checks passed for {recommendation.pair}: "
                         f"confidence={recommendation.confidence:.2f}, "
                         f"signal={recommendation.signal}")
        return True
    
    def _create_rejected_decision(
        self, 
        recommendation: TradeRecommendation, 
        risk_assessment: Dict[str, Any]
    ) -> TradeDecision:
        """Create a rejected trade decision."""
        return TradeDecision(
            recommendation=recommendation,
            approved=False,
            risk_management_notes=risk_assessment['reason'],
            timestamp=datetime.now(timezone.utc)
        )
    
    async def validate_market_conditions(
        self, 
        recommendation: TradeRecommendation,
        market_context: Any
    ) -> Dict[str, Any]:
        """Validate market conditions for the trade."""
        
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check market condition alignment
            if recommendation.market_condition != market_context.condition:
                validation['warnings'].append(
                    f"Market condition mismatch: AI detected {recommendation.market_condition.value}, "
                    f"but system detected {market_context.condition.value}"
                )
            
            # Check volatility conditions
            if market_context.condition == MarketCondition.NEWS_REACTIONARY:
                if recommendation.estimated_hold_time > timedelta(minutes=30):
                    validation['warnings'].append(
                        "News reactionary market: consider shorter hold time"
                    )
            
            # Check trend strength for reversal trades
            if market_context.condition == MarketCondition.REVERSAL:
                if market_context.trend_strength < 0.5:
                    validation['warnings'].append(
                        "Low trend strength for reversal trade"
                    )
            
            # Check breakout confirmation
            if market_context.condition == MarketCondition.BREAKOUT:
                if not self._confirm_breakout(recommendation, market_context):
                    validation['warnings'].append(
                        "Breakout not confirmed with volume/momentum"
                    )
            
            # Check ranging market conditions
            if market_context.condition == MarketCondition.RANGING:
                if recommendation.risk_reward_ratio < 1.5:
                    validation['warnings'].append(
                        "Low risk-reward ratio for ranging market"
                    )
            
            # Check for extreme market conditions
            if market_context.volatility > self.config.max_volatility_threshold:
                validation['errors'].append(
                    f"Volatility too high: {market_context.volatility:.4f}"
                )
                validation['valid'] = False
            
            # Check for low liquidity conditions
            if self._is_low_liquidity_time():
                validation['warnings'].append(
                    "Low liquidity period detected"
                )
            
        except Exception as e:
            validation['errors'].append(f"Error validating market conditions: {e}")
            validation['valid'] = False
        
        return validation
    
    def _confirm_breakout(self, recommendation: TradeRecommendation, market_context: Any) -> bool:
        """Confirm breakout with additional criteria."""
        # This would check for volume confirmation, momentum, etc.
        # For now, return True as placeholder
        return True
    
    def _is_low_liquidity_time(self) -> bool:
        """Check if current time is during low liquidity period."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return True
        
        # Late Friday or early Monday
        if now.weekday() == 4 and now.hour >= 20:  # Friday after 8 PM UTC
            return True
        if now.weekday() == 0 and now.hour <= 8:  # Monday before 8 AM UTC
            return True
        
        return False
    
    async def update_position_status(
        self, 
        pair: str, 
        status: str, 
        execution_price: Optional[Decimal] = None
    ) -> None:
        """Update the status of an open position."""
        
        if pair in self._open_positions:
            decision = self._open_positions[pair]
            
            if status == "opened":
                # Position was opened
                self.logger.info(f"Position opened for {pair} at {execution_price}")
            
            elif status == "closed":
                # Position was closed
                closed_decision = self._open_positions.pop(pair)
                await self.performance_tracker.record_trade(closed_decision, execution_price)
                self.logger.info(f"Position closed for {pair} at {execution_price}")
            
            elif status == "cancelled":
                # Position was cancelled
                self._open_positions.pop(pair)
                self.logger.info(f"Position cancelled for {pair}")
    
    def _log_decision(self, decision: TradeDecision) -> None:
        """Log trade decision for analysis."""
        
        log_entry = {
            'timestamp': decision.timestamp.isoformat(),
            'pair': decision.recommendation.pair,
            'signal': decision.recommendation.signal.value,
            'approved': decision.approved,
            'confidence': decision.recommendation.confidence,
            'market_condition': decision.recommendation.market_condition.value,
            'entry_price': float(decision.recommendation.entry_price) if decision.recommendation.entry_price else None,
            'stop_loss': float(decision.recommendation.stop_loss) if decision.recommendation.stop_loss else None,
            'take_profit': float(decision.recommendation.take_profit) if decision.recommendation.take_profit else None,
            'position_size': float(decision.position_size) if decision.position_size else None,
            'risk_amount': float(decision.risk_amount) if decision.risk_amount else None,
            'reasoning': decision.recommendation.reasoning,
            'risk_notes': decision.risk_management_notes
        }
        
        self.logger.info(f"Trade decision logged: {json.dumps(log_entry, indent=2)}")
    
    async def get_daily_performance(self) -> PerformanceMetrics:
        """Get daily performance metrics."""
        return await self.performance_tracker.get_daily_metrics()
    
    async def get_open_positions(self) -> Dict[str, TradeDecision]:
        """Get currently open positions."""
        return self._open_positions.copy()
    
    async def cleanup_old_data(self) -> None:
        """Clean up old decision data."""
        try:
            # Remove decisions older than 7 days
            from datetime import datetime, timezone
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            self._daily_trades = [
                d for d in self._daily_trades 
                if d.timestamp > cutoff_date
            ]
            
            # Clean up old decision times
            old_pairs = [
                pair for pair, time in self._last_decision_time.items()
                if time < cutoff_date
            ]
            for pair in old_pairs:
                del self._last_decision_time[pair]
            
            self.logger.info(f"Cleaned up {len(old_pairs)} old decision records")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old decision data: {e}")
    
    async def reset_daily_limits(self) -> None:
        """Reset daily trading limits."""
        try:
            # Clear daily trades list
            self._daily_trades.clear()
            
            # Clear open positions (in case of system restart)
            self._open_positions.clear()
            
            self.logger.info("Daily trading limits reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting daily limits: {e}")
    
    async def start(self) -> None:
        """Start the decision layer."""
        try:
            print("🎯 [DEBUG] Starting decision layer...")
            self.logger.info("Starting decision layer...")
            
            # Start trade recorder
            print("📝 [DEBUG] Starting trade recorder...")
            await self.trade_recorder.start()
            print("✅ [DEBUG] Trade recorder started")
            
            # Initialize performance tracker
            print("📊 [DEBUG] Starting performance tracker...")
            await self.performance_tracker.start()
            print("✅ [DEBUG] Performance tracker started")
            
            print("✅ [DEBUG] Decision layer started successfully")
            self.logger.info("Decision layer started successfully")
        except Exception as e:
            print(f"❌ [DEBUG] Error starting decision layer: {e}")
            print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
            self.logger.error(f"Error starting decision layer: {e}")
            raise
    
    async def close(self) -> None:
        """Close decision layer."""
        try:
            # Stop trade recorder
            await self.trade_recorder.stop()
            await self.performance_tracker.close()
            self.logger.info("Decision layer closed")
        except Exception as e:
            self.logger.error(f"Error closing decision layer: {e}") 

    async def make_enhanced_decision(self, pair: str, recommendation: Optional[TradeRecommendation], 
                                   technical_indicators: Optional[TechnicalIndicators],
                                   fundamental_analysis: Dict[str, Any], 
                                   regime_analysis: Dict[str, Any],
                                   market_context: MarketContext) -> Optional[TradeDecision]:
        """Make enhanced trading decision based on all available data."""
        self.logger.info(f"🎯 Starting enhanced decision making for {pair}...")
        
        try:
            if not recommendation:
                self.logger.info(f"ℹ️ {pair}: No trade recommendation - waiting for better market conditions")
                return None
            
            self.logger.info(f"📊 {pair}: Analyzing recommendation - Signal: {recommendation.signal}, Confidence: {recommendation.confidence}")
            
            # Check confidence threshold
            if recommendation.confidence < self.config.technical_analysis.confidence_threshold:
                self.logger.info(
                    f"❌ {pair}: Confidence {recommendation.confidence} below threshold {self.config.technical_analysis.confidence_threshold}"
                )
                return None
            
            self.logger.info(f"✅ {pair}: Confidence threshold met")
            
            # Create decision
            # Create canonical TradeDecision as defined in core.models
            from datetime import datetime, timezone
            decision = TradeDecision(
                recommendation=recommendation,
                approved=True,
                position_size=None,
                risk_amount=None,
                modified_stop_loss=recommendation.stop_loss,
                modified_take_profit=recommendation.take_profit,
                risk_management_notes="",
                timestamp=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"✅ {pair}: Decision created successfully")
            self.logger.info(f"🎯 {pair}: Decision - Signal: {decision.recommendation.signal}, Entry: {decision.recommendation.entry_price}, SL: {decision.modified_stop_loss}, TP: {decision.modified_take_profit}")
            
            # Record decision
            self._log_decision(decision)
            
            return decision
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced decision making for {pair}: {e}")
            return None 