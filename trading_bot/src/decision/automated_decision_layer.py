"""
Automated Decision Layer - Fully automated trading without human intervention.
Sends notifications for trade entry/exit with detailed reasoning.
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
from .risk_manager_improved import ImprovedRiskManager as RiskManager
from .performance_tracker import PerformanceTracker
from .enhanced_excel_trade_recorder import EnhancedExcelTradeRecorder


class AutomatedDecisionLayer:
    """Fully automated decision layer with automatic trade execution and detailed notifications."""
    
    def __init__(self, config: Config, notification_layer=None, position_manager=None):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.risk_manager = RiskManager(config)
        self.performance_tracker = PerformanceTracker()
        self.trade_recorder = EnhancedExcelTradeRecorder(config)
        
        # External components for automation
        self.notification_layer = notification_layer
        self.position_manager = position_manager
        
        # Decision tracking
        self._daily_trades: List[TradeDecision] = []
        self._open_positions: Dict[str, TradeDecision] = {}
        self._last_decision_time: Dict[str, datetime] = {}
        
        # Performance metrics
        self._performance_metrics = PerformanceMetrics()
        
        # Trade execution tracking
        self._pending_executions: Dict[str, TradeDecision] = {}
        self._execution_history: List[Dict[str, Any]] = []
    
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
        """Process AI recommendation and automatically execute if approved."""
        
        try:
            # Check if we should process this recommendation
            if not await self._should_process_recommendation(recommendation):
                self.logger.info(
                    f"🚫 Skipping recommendation for {recommendation.pair}: "
                    f"confidence {recommendation.confidence:.2f} below threshold "
                    f"({self.config.ai_confidence_threshold})"
                )
                return None
            
            # Apply risk management rules
            fundamental_analysis = ai_outputs.get('fundamental_analysis') if ai_outputs else None
            risk_assessment = await self.risk_manager.assess_risk(
                recommendation, current_price, market_context, fundamental_analysis
            )
            
            # Ensure risk_assessment has all required fields
            if 'notes' not in risk_assessment:
                risk_assessment['notes'] = risk_assessment.get('reason', 'Risk assessment completed')
            
            if not risk_assessment['approved']:
                self.logger.info(f"⚠️ Risk management rejected trade for {recommendation.pair}: "
                               f"{risk_assessment['reason']}")
                
                # Send rejection notification
                await self._send_rejection_notification(recommendation, risk_assessment)
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
            
            # Automatically execute the trade
            trade_id = await self._execute_trade_automatically(decision, market_context)
            
            # Set trade_id in decision for tracking
            decision.trade_id = trade_id
            
            if trade_id and not trade_id.startswith('FAILED-') and not trade_id.startswith('ERROR-'):
                # Send execution notification only after successful execution
                await self._send_execution_notification(decision, trade_id, risk_assessment)
                
                # Update tracking
                self._daily_trades.append(decision)
                self._last_decision_time[recommendation.pair] = datetime.now(timezone.utc)
                self._open_positions[recommendation.pair] = decision
                
                # Update risk manager with the new open position
                position_added = self.risk_manager.add_open_position(recommendation.pair, {
                    'trade_id': trade_id,
                    'pair': recommendation.pair,
                    'signal': recommendation.signal.value,
                    'entry_price': float(recommendation.entry_price),
                    'position_size': float(position_size['size']),
                    'risk_amount': float(position_size['risk_amount'])
                })
                
                if not position_added:
                    self.logger.warning(f"Failed to add position to risk manager for {recommendation.pair}")
                
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
                
                self.logger.info(f"✅ Trade EXECUTED for {recommendation.pair}: "
                               f"{recommendation.signal.value} at {current_price}, Trade ID: {trade_id}")
                
                return decision
            else:
                # Send execution failure notification
                await self._send_execution_failure_notification(decision, "Failed to execute trade")
                return None
            
        except Exception as e:
            self.logger.error(f"Error processing recommendation for {recommendation.pair}: {e}")
            await self._send_error_notification(recommendation, str(e))
            return None
    
    async def _execute_trade_automatically(self, decision: TradeDecision, market_context: Any) -> Optional[str]:
        """Automatically execute a trade without human intervention."""
        try:
            if not self.position_manager:
                self.logger.error("Position manager not available for automatic execution")
                return None
            
            # Execute the trade
            trade_id = await self.position_manager.execute_trade(decision, market_context)
            
            # Record execution
            execution_record = {
                'timestamp': datetime.now(timezone.utc),
                'trade_id': trade_id,
                'pair': decision.recommendation.pair,
                'signal': decision.recommendation.signal.value,
                'entry_price': decision.recommendation.entry_price,
                'position_size': decision.position_size,
                'status': 'executed' if trade_id else 'failed'
            }
            self._execution_history.append(execution_record)
            
            return trade_id
            
        except Exception as e:
            self.logger.error(f"Error executing trade automatically: {e}")
            return None
    
    async def _send_pre_execution_notification(self, decision: TradeDecision, risk_assessment: Dict[str, Any],
                                             technical_indicators: Dict[TimeFrame, TechnicalIndicators] = None,
                                             market_context: Any = None):
        """Send notification before trade execution."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
🚀 TRADE EXECUTED

📊 {decision.recommendation.pair} {decision.recommendation.signal.value.upper()}
💰 Entry: {decision.recommendation.entry_price}
🛑 Stop: {decision.modified_stop_loss}
🎯 Target: {decision.modified_take_profit}
📈 Size: {decision.position_size:.0f} units

⏰ {datetime.now().strftime('%H:%M:%S')}
""".strip()
            
            await self.notification_layer.send_trade_alert(
                decision, 
                chart_data={'type': 'pre_execution'},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending pre-execution notification: {e}")
    
    async def _send_execution_notification(self, decision: TradeDecision, trade_id: str, risk_assessment: Dict[str, Any]):
        """Send notification after successful trade execution."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
✅ TRADE EXECUTED SUCCESSFULLY

📊 Execution Details:
• Trade ID: {trade_id}
• Pair: {decision.recommendation.pair}
• Signal: {decision.recommendation.signal.value.upper()}
• Entry Price: {decision.recommendation.entry_price}
• Stop Loss: {decision.modified_stop_loss}
• Take Profit: {decision.modified_take_profit}
• Position Size: {decision.position_size:.2f}
• Risk Amount: ${decision.risk_amount:.2f}

🎯 Execution Summary:
• Status: ✅ EXECUTED
• Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
• Risk Score: {risk_assessment.get('risk_score', 0):.2f}

💡 Trade Reasoning:
{decision.recommendation.reasoning}

📈 Next Steps:
• Monitor position for stop loss or take profit
• Position will be automatically managed
• You will receive exit notifications

🔒 Risk Management Applied:
{decision.risk_management_notes}
""".strip()
            
            await self.notification_layer.send_trade_alert(
                decision, 
                chart_data={'type': 'execution_success', 'trade_id': trade_id},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending execution notification: {e}")
    
    async def _send_rejection_notification(self, recommendation: TradeRecommendation, risk_assessment: Dict[str, Any]):
        """Send notification for rejected trades."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
❌ TRADE REJECTED

📊 Rejected Trade:
• Pair: {recommendation.pair}
• Signal: {recommendation.signal.value.upper()}
• Entry Price: {recommendation.entry_price}
• Confidence: {recommendation.confidence:.1%}

🚫 Rejection Reason:
{risk_assessment['reason']}

🔍 Risk Assessment:
• Risk Score: {risk_assessment.get('risk_score', 0):.2f}
• Risk Notes: {risk_assessment.get('notes', 'N/A')}

💡 AI Reasoning (for reference):
{recommendation.reasoning}

⏰ Rejected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
            
            # Create a temporary decision for notification
            temp_decision = TradeDecision(
                recommendation=recommendation,
                approved=False,
                position_size=None,
                risk_amount=None,
                modified_stop_loss=recommendation.stop_loss,
                modified_take_profit=recommendation.take_profit,
                risk_management_notes=risk_assessment['reason'],
                timestamp=datetime.now(timezone.utc)
            )
            
            await self.notification_layer.send_trade_alert(
                temp_decision, 
                chart_data={'type': 'rejection'},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending rejection notification: {e}")
    
    async def _send_execution_failure_notification(self, decision: TradeDecision, failure_reason: str):
        """Send notification for execution failures."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
⚠️ TRADE EXECUTION FAILED

📊 Failed Trade:
• Pair: {decision.recommendation.pair}
• Signal: {decision.recommendation.signal.value.upper()}
• Entry Price: {decision.recommendation.entry_price}
• Position Size: {decision.position_size:.2f}

❌ Failure Reason:
{failure_reason}

🔧 Technical Details:
• Decision was approved by risk management
• Position sizing was calculated correctly
• Execution failed at broker level

⏰ Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
            
            await self.notification_layer.send_trade_alert(
                decision, 
                chart_data={'type': 'execution_failure'},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending execution failure notification: {e}")
    
    async def _send_error_notification(self, recommendation: TradeRecommendation, error_message: str):
        """Send notification for processing errors."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
🚨 PROCESSING ERROR

📊 Affected Trade:
• Pair: {recommendation.pair}
• Signal: {recommendation.signal.value.upper()}
• Entry Price: {recommendation.entry_price}

❌ Error Details:
{error_message}

🔧 System Status:
• Decision layer encountered an error
• Trade was not processed
• System will continue with next recommendation

⏰ Error at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
            
            # Create a temporary decision for notification
            temp_decision = TradeDecision(
                recommendation=recommendation,
                approved=False,
                position_size=None,
                risk_amount=None,
                modified_stop_loss=recommendation.stop_loss,
                modified_take_profit=recommendation.take_profit,
                risk_management_notes=f"Processing error: {error_message}",
                timestamp=datetime.now(timezone.utc)
            )
            
            await self.notification_layer.send_trade_alert(
                temp_decision, 
                chart_data={'type': 'processing_error'},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
    
    def _format_technical_indicators(self, indicators: Any) -> str:
        """Format technical indicators for notification."""
        if not indicators:
            return "N/A"
        
        formatted = []
        
        # Handle single TechnicalIndicators object
        if hasattr(indicators, 'rsi') and hasattr(indicators, 'macd'):
            formatted.append(f"• RSI={indicators.rsi:.2f}, MACD={indicators.macd:.5f}")
            if hasattr(indicators, 'bollinger_upper') and indicators.bollinger_upper:
                formatted.append(f"• Bollinger: Upper={indicators.bollinger_upper:.5f}, Lower={indicators.bollinger_lower:.5f}")
            if hasattr(indicators, 'ema_fast') and indicators.ema_fast:
                formatted.append(f"• EMA: Fast={indicators.ema_fast:.5f}, Slow={indicators.ema_slow:.5f}")
            if hasattr(indicators, 'atr') and indicators.atr:
                formatted.append(f"• ATR={indicators.atr:.5f}")
        
        # Handle dictionary of indicators by timeframe
        elif isinstance(indicators, dict):
            for timeframe, indicator in indicators.items():
                if hasattr(indicator, 'rsi') and hasattr(indicator, 'macd'):
                    formatted.append(f"• {timeframe.value}: RSI={indicator.rsi:.2f}, MACD={indicator.macd:.5f}")
                    if hasattr(indicator, 'bollinger_upper') and indicator.bollinger_upper:
                        formatted.append(f"  Bollinger: Upper={indicator.bollinger_upper:.5f}, Lower={indicator.bollinger_lower:.5f}")
                    if hasattr(indicator, 'ema_fast') and indicator.ema_fast:
                        formatted.append(f"  EMA: Fast={indicator.ema_fast:.5f}, Slow={indicator.ema_slow:.5f}")
                    if hasattr(indicator, 'atr') and indicator.atr:
                        formatted.append(f"  ATR={indicator.atr:.5f}")
        
        # Handle list of indicators
        elif isinstance(indicators, list):
            for i, indicator in enumerate(indicators):
                if hasattr(indicator, 'rsi') and hasattr(indicator, 'macd'):
                    formatted.append(f"• Indicator {i+1}: RSI={indicator.rsi:.2f}, MACD={indicator.macd:.5f}")
        
        # Handle unknown format
        else:
            formatted.append(f"• Indicators: {str(indicators)[:100]}...")
        
        return "\n".join(formatted) if formatted else "N/A"
    
    def _format_market_context(self, market_context: Any) -> str:
        """Format market context for notification."""
        if not market_context:
            return "N/A"
        
        return f"""• Condition: {market_context.condition.value}
• Volatility: {market_context.volatility:.4f}
• Trend Strength: {market_context.trend_strength:.2f}
• News Sentiment: {market_context.news_sentiment}"""
    
    async def _should_process_recommendation(self, recommendation: TradeRecommendation) -> bool:
        """Check if recommendation meets basic criteria for processing."""
        
        # Check confidence threshold
        if recommendation.confidence < self.config.ai_confidence_threshold:
            self.logger.debug(f"🔍 Confidence check failed for {recommendation.pair}: "
                            f"{recommendation.confidence:.2f} < {self.config.ai_confidence_threshold}")
            return False
        
        # Check if we already have a recent decision for this pair
        if recommendation.pair in self._last_decision_time:
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
        
        # Check if we have an open position for this pair (check both local and actual positions)
        if recommendation.pair in self._open_positions:
            self.logger.info(f"🚫 Skipping {recommendation.pair}: Already have open position in local tracking")
            return False
        
        # Check actual open positions from position manager
        if self.position_manager:
            try:
                position_summary = await self.position_manager.get_position_summary()
                actual_open_positions = position_summary.get('open_positions', {})
                if recommendation.pair in actual_open_positions:
                    self.logger.info(f"🚫 Skipping {recommendation.pair}: Already have active trade (Position Manager)")
                    return False
            except Exception as e:
                self.logger.warning(f"Error checking actual positions for {recommendation.pair}: {e}")
        
        # Also check risk manager's open positions
        try:
            risk_open_positions = self.risk_manager._shared_risk_data.get('open_positions', {})
            if recommendation.pair in risk_open_positions:
                self.logger.info(f"🚫 Skipping {recommendation.pair}: Already have active trade (Risk Manager)")
                return False
        except Exception as e:
            self.logger.warning(f"Error checking risk manager positions for {recommendation.pair}: {e}")
        
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
    
    async def update_position_status(
        self, 
        pair: str, 
        status: str, 
        execution_price: Optional[Decimal] = None,
        exit_reason: Optional[str] = None
    ) -> None:
        """Update the status of an open position and send notifications."""
        
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
                
                # Remove from risk manager tracking
                try:
                    if pair in self.risk_manager._shared_risk_data.get('open_positions', {}):
                        del self.risk_manager._shared_risk_data['open_positions'][pair]
                        self.logger.info(f"Removed {pair} from risk manager tracking")
                except Exception as e:
                    self.logger.warning(f"Error removing {pair} from risk manager: {e}")
                
                # Send exit notification
                await self._send_exit_notification(closed_decision, execution_price, exit_reason)
            
            elif status == "cancelled":
                # Position was cancelled
                cancelled_decision = self._open_positions.pop(pair)
                self.logger.info(f"Position cancelled for {pair}")
                
                # Send cancellation notification
                await self._send_cancellation_notification(cancelled_decision, exit_reason)
    
    async def _send_exit_notification(self, decision: TradeDecision, exit_price: Decimal, exit_reason: str):
        """Send notification when a position is closed."""
        try:
            if not self.notification_layer:
                return
            
            # Calculate P&L
            entry_price = decision.recommendation.entry_price
            if entry_price and exit_price:
                if decision.recommendation.signal == TradeSignal.BUY:
                    pnl = (exit_price - entry_price) * decision.position_size
                else:
                    pnl = (entry_price - exit_price) * decision.position_size
                pnl_str = f"${pnl:.2f}"
                pnl_emoji = "📈" if pnl > 0 else "📉"
            else:
                pnl_str = "N/A"
                pnl_emoji = "❓"
            
            message = f"""
{pnl_emoji} POSITION CLOSED

📊 Exit Details:
• Pair: {decision.recommendation.pair}
• Signal: {decision.recommendation.signal.value.upper()}
• Entry Price: {decision.recommendation.entry_price}
• Exit Price: {exit_price}
• Position Size: {decision.position_size:.2f}
• P&L: {pnl_str}

🎯 Exit Reason:
{exit_reason}

📈 Trade Summary:
• Hold Time: {datetime.now(timezone.utc) - decision.timestamp}
• Risk Amount: ${decision.risk_amount:.2f}
• Risk/Reward: {decision.recommendation.risk_reward_ratio:.2f}

⏰ Closed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
            
            await self.notification_layer.send_trade_alert(
                decision, 
                chart_data={'type': 'position_closed', 'exit_price': float(exit_price), 'pnl': pnl_str},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending exit notification: {e}")
    
    async def _send_cancellation_notification(self, decision: TradeDecision, cancellation_reason: str):
        """Send notification when a position is cancelled."""
        try:
            if not self.notification_layer:
                return
            
            message = f"""
❌ POSITION CANCELLED

📊 Cancelled Trade:
• Pair: {decision.recommendation.pair}
• Signal: {decision.recommendation.signal.value.upper()}
• Entry Price: {decision.recommendation.entry_price}
• Position Size: {decision.position_size:.2f}

🚫 Cancellation Reason:
{cancellation_reason}

⏰ Cancelled at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
""".strip()
            
            await self.notification_layer.send_trade_alert(
                decision, 
                chart_data={'type': 'position_cancelled'},
                custom_message=message
            )
            
        except Exception as e:
            self.logger.error(f"Error sending cancellation notification: {e}")
    
    async def get_daily_performance(self) -> PerformanceMetrics:
        """Get daily performance metrics."""
        return await self.performance_tracker.get_daily_metrics()
    
    async def get_open_positions(self) -> Dict[str, TradeDecision]:
        """Get currently open positions."""
        return self._open_positions.copy()
    
    async def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history."""
        return self._execution_history.copy()
    
    async def cleanup_old_data(self) -> None:
        """Clean up old decision data."""
        try:
            # Remove decisions older than 7 days
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
            
            # Clean up old execution history
            self._execution_history = [
                record for record in self._execution_history
                if record['timestamp'] > cutoff_date
            ]
            
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
        """Start the automated decision layer."""
        try:
            print("🤖 [DEBUG] Starting automated decision layer...")
            self.logger.info("Starting automated decision layer...")
            
            # Start trade recorder
            print("📝 [DEBUG] Starting trade recorder...")
            await self.trade_recorder.start()
            print("✅ [DEBUG] Trade recorder started")
            
            # Initialize performance tracker
            print("📊 [DEBUG] Starting performance tracker...")
            await self.performance_tracker.start()
            print("✅ [DEBUG] Performance tracker started")
            
            print("✅ [DEBUG] Automated decision layer started successfully")
            self.logger.info("Automated decision layer started successfully")
        except Exception as e:
            print(f"❌ [DEBUG] Error starting automated decision layer: {e}")
            print(f"❌ [DEBUG] Traceback: {traceback.format_exc()}")
            self.logger.error(f"Error starting automated decision layer: {e}")
            raise
    
    async def close(self) -> None:
        """Close automated decision layer."""
        try:
            # Stop trade recorder
            await self.trade_recorder.stop()
            await self.performance_tracker.close()
            self.logger.info("Automated decision layer closed")
        except Exception as e:
            self.logger.error(f"Error closing automated decision layer: {e}")
