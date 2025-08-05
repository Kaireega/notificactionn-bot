#!/usr/bin/env python3
"""
Market Adaptive Trading Bot - Main Entry Point
Enhanced with Position Management, Fundamental Analysis, Advanced Risk Management, and Market Regime Detection.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add the project root to the path for imports
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.utils.logger import get_logger
from trading_bot.src.data.data_layer import DataLayer
from trading_bot.src.ai.ai_analysis_layer import AIAnalysisLayer
from trading_bot.src.decision.decision_layer import DecisionLayer
from trading_bot.src.notifications.notification_layer import NotificationLayer
from trading_bot.src.core.position_manager import PositionManager
from trading_bot.src.core.fundamental_analyzer import FundamentalAnalyzer
from trading_bot.src.core.advanced_risk_manager import AdvancedRiskManager
from trading_bot.src.core.market_regime_detector import MarketRegimeDetector
from api.oanda_api import OandaApi


class TradingBot:
    """Enhanced Market Adaptive Trading Bot with all advanced components."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Load configuration
        self.config = Config()
        
        # Initialize OANDA API
        self.oanda_api = OandaApi()
            
        # Initialize core components
        self.data_layer = DataLayer(self.config)
        self.ai_layer = AIAnalysisLayer(self.config)
        self.decision_layer = DecisionLayer(self.config)
        self.notification_layer = NotificationLayer(self.config)
            
        # Initialize new advanced components
        self.position_manager = PositionManager(self.config, self.oanda_api)
        self.fundamental_analyzer = FundamentalAnalyzer(self.config)
        self.advanced_risk_manager = AdvancedRiskManager(self.config)
        self.market_regime_detector = MarketRegimeDetector(self.config)
        
        # Bot state
        self.is_running = False
        self.loop_count = 0
    
    async def start(self):
        """Start the enhanced trading bot."""
        try:
            self.logger.info("Starting Enhanced Market Adaptive Trading Bot...")
            
            # Start all components
            await self.data_layer.start()
            await self.ai_layer.start()
            await self.decision_layer.start()
            await self.notification_layer.start()
            
            # Start new advanced components
            await self.position_manager.start()
            await self.fundamental_analyzer.start()
            await self.advanced_risk_manager.start()
            await self.market_regime_detector.start()
            
            self.logger.info("All components initialized successfully")
            
            # Send startup notification
            await self._send_startup_message()
            
            # Start main trading loop
            self.is_running = True
            await self._enhanced_trading_loop()
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            raise

    async def _send_startup_message(self):
        """Send enhanced startup message with all component status."""
        try:
            # Get component summaries
            position_summary = await self.position_manager.get_position_summary()
            fundamental_summary = await self.fundamental_analyzer.get_fundamental_summary()
            risk_summary = await self.advanced_risk_manager.get_risk_summary()
            regime_summary = await self.market_regime_detector.get_regime_summary()

            startup_message = f"""
🤖 Enhanced Trading Bot Started Successfully

📊 Component Status:
✅ Data Layer: Active
✅ AI Analysis: Active  
✅ Decision Layer: Active
✅ Notifications: Active
✅ Position Manager: Active
✅ Fundamental Analyzer: Active
✅ Advanced Risk Manager: Active
✅ Market Regime Detector: Active

🎯 Configuration:
• Trading Pairs: {', '.join(self.config.trading_pairs)}
• Multi-timeframe Analysis: {', '.join([tf.value for tf in self.config.timeframes])}
• Risk Management: {self.config.trading.risk_percentage}% per trade
• Daily Loss Limit: {self.config.risk_management.max_daily_loss}%

📈 Advanced Features:
• Real-time Position Monitoring
• Economic Calendar Integration
• Kelly Criterion Position Sizing
• Market Regime Detection
• Dynamic Strategy Adaptation
• Portfolio Heat Management

🔄 Current Status:
• Active Positions: {position_summary['active_positions']}
• Daily P&L: ${position_summary['daily_pnl']:.2f}
• Current Regime: {regime_summary['current_regime']}
• Risk Score: {risk_summary.get('current_drawdown', 0):.2%}

Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
            
            await self.notification_layer.send_notification(
                message=startup_message,
                notification_type="STARTUP"
            )
            self.logger.info("Enhanced startup notification sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending startup message: {e}")
    
    async def _enhanced_trading_loop(self):
        """Enhanced main trading loop with all advanced components."""
        while self.is_running:
            try:
                self.loop_count += 1
                loop_start_time = datetime.now()
                
                # Initialize enhanced loop tracking
                loop_stats = {
                    'loop_number': self.loop_count,
                    'start_time': loop_start_time,
                    'pairs_analyzed': [],
                    'ai_analyses_performed': 0,
                    'recommendations_generated': 0,
                    'trades_approved': 0,
                    'trades_rejected': 0,
                    'errors_encountered': [],
                    'market_conditions_observed': {},
                    'technical_indicators_calculated': 0,
                    'data_points_processed': 0,
                    'fundamental_analyses': 0,
                    'regime_detections': 0,
                    'risk_assessments': 0
                }
                
                # Get data for all pairs
                all_data = await self.data_layer.get_all_pairs_data()
                
                for pair, data in all_data.items():
                    # Check if we should analyze this pair
                    if self._should_analyze_pair(pair):
                        loop_stats['pairs_analyzed'].append(pair)
                        loop_stats['data_points_processed'] += len(data.get('candles', []))
                        
                        # Get candles for all timeframes
                        candles_by_timeframe = {}
                        for timeframe in self.config.timeframes:
                            candles = await self.data_layer.get_candles(pair, timeframe, 100)
                            if candles:
                                candles_by_timeframe[timeframe] = candles
                                self.logger.info(f"📊 {pair} {timeframe.value}: Retrieved {len(candles)} candles")
                            else:
                                self.logger.warning(f"⚠️ {pair} {timeframe.value}: No candles retrieved")
                        
                        if len(candles_by_timeframe) >= 2:  # Need at least 2 timeframes
                            # Get market context
                            market_context = data['market_context']
                            
                            # Track market condition
                            condition = market_context.condition.value
                            if condition not in loop_stats['market_conditions_observed']:
                                loop_stats['market_conditions_observed'][condition] = 0
                            loop_stats['market_conditions_observed'][condition] += 1
                            
                            # Track technical indicators calculated
                            loop_stats['technical_indicators_calculated'] += len(candles_by_timeframe) * 6
                            
                            # 🔥 NEW: Market Regime Detection
                            regime_analysis = await self.market_regime_detector.detect_regime(
                                pair, candles_by_timeframe.get(self.config.timeframes[1], []), 
                                market_context, None  # Will be filled by AI layer
                            )
                            loop_stats['regime_detections'] += 1
                            
                            # 🔥 NEW: Fundamental Analysis
                            fundamental_analysis = await self.fundamental_analyzer.analyze_fundamentals(
                                pair, market_context
                            )
                            loop_stats['fundamental_analyses'] += 1
                            
                            # Perform multi-timeframe analysis
                            recommendation, technical_indicators = await self.ai_layer.analyze_multiple_timeframes(
                                pair, candles_by_timeframe, market_context
                            )
                            
                            loop_stats['ai_analyses_performed'] += 1
                            
                            # Log AI analysis results for debugging
                            if recommendation:
                                self.logger.info(f"🎯 AI Analysis for {pair}: "
                                               f"Signal={recommendation.signal.value}, "
                                               f"Confidence={recommendation.confidence:.2f}, "
                                               f"RR={recommendation.risk_reward_ratio:.2f}")
                                
                                if recommendation.confidence > 0.6:
                                    self.logger.info(f"✅ Recommendation meets confidence threshold for {pair}")
                                    loop_stats['recommendations_generated'] += 1
                                else:
                                    self.logger.debug(f"❌ Recommendation below confidence threshold for {pair}: "
                                                   f"{recommendation.confidence:.2f} < 0.6")
                            else:
                                self.logger.debug(f"❌ No AI recommendation generated for {pair}")
                            
                            if recommendation and recommendation.confidence > 0.6:
                                # Get current price
                                current_price = data['current_price']
                                if current_price:
                                    # 🔥 NEW: Advanced Risk Assessment
                                    risk_assessment = await self.advanced_risk_manager.assess_trade_risk(
                                        recommendation, market_context, technical_indicators, fundamental_analysis
                                    )
                                    loop_stats['risk_assessments'] += 1
                                    
                                    if risk_assessment['approved']:
                                        # Create enhanced trade decision
                                        decision = await self._create_enhanced_decision(
                                            recommendation, current_price, market_context,
                                            technical_indicators, fundamental_analysis, 
                                            regime_analysis, risk_assessment
                                        )
                                        
                                        if decision:
                                            # 🔥 NEW: Execute trade through Position Manager
                                            trade_id = await self.position_manager.execute_trade(
                                                decision, market_context
                                            )
                                            
                                            if trade_id:
                                                loop_stats['trades_approved'] += 1
                                                self.logger.info(f"✅ Trade executed: {pair} (ID: {trade_id})")
                                                
                                                # Send enhanced trade notification
                                                await self._send_enhanced_trade_notification(
                                                    decision, trade_id, fundamental_analysis, regime_analysis
                                                )
                                            else:
                                                self.logger.warning(f"⚠️ Trade execution failed: {pair}")
                                                loop_stats['trades_rejected'] += 1
                                        else:
                                            self.logger.debug(f"❌ Decision creation failed: {pair}")
                                            loop_stats['trades_rejected'] += 1
                                    else:
                                        self.logger.info(f"🚫 Risk assessment rejected: {pair} - {risk_assessment['reason']}")
                                        loop_stats['trades_rejected'] += 1
                
                # Generate and send enhanced loop report
                await self._send_enhanced_loop_report(loop_stats)
                
                # Wait for next loop
                await asyncio.sleep(self.config.data_update_frequency)
                
            except Exception as e:
                self.logger.error(f"Error in enhanced trading loop: {e}")
                loop_stats['errors_encountered'].append(str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _create_enhanced_decision(self, recommendation, current_price, market_context,
                                      technical_indicators, fundamental_analysis, 
                                      regime_analysis, risk_assessment):
        """Create enhanced trade decision with all analysis data."""
        try:
            # Use existing decision layer but with enhanced data
            decision = await self.decision_layer.process_recommendation(
                recommendation, current_price, market_context,
                technical_indicators=technical_indicators,
                candles_by_timeframe={},  # Will be filled if needed
                ai_outputs={
                    'fundamental_analysis': fundamental_analysis,
                    'regime_analysis': regime_analysis,
                    'risk_assessment': risk_assessment
                },
                multi_timeframe_analysis={},
                risk_assessment=risk_assessment,
                raw_data={}
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error creating enhanced decision: {e}")
            return None
    
    async def _send_enhanced_trade_notification(self, decision, trade_id, 
                                              fundamental_analysis, regime_analysis):
        """Send enhanced trade notification with all analysis data."""
        try:
            notification_message = f"""
🎯 ENHANCED TRADE EXECUTED

📊 Trade Details:
• Pair: {decision.recommendation.pair}
• Signal: {decision.recommendation.signal.value.upper()}
• Entry: {decision.recommendation.entry_price}
• Stop Loss: {decision.modified_stop_loss}
• Take Profit: {decision.modified_take_profit}
• Position Size: {decision.position_size:.2f}
• Risk Amount: ${decision.risk_amount:.2f}

🔍 Market Analysis:
• Market Condition: {decision.recommendation.market_condition.value}
• Regime: {regime_analysis['regime']} (Confidence: {regime_analysis['confidence']:.2f})
• Fundamental Score: {fundamental_analysis['fundamental_score']:.2f}
• Session: {fundamental_analysis['current_session']}

⚡ Risk Management:
• Kelly Criterion: {decision.risk_management_notes}
• Portfolio Heat: {fundamental_analysis.get('correlation_analysis', {}).get('portfolio_heat', 0):.2f}
• Position Multiplier: {fundamental_analysis['position_size_multiplier']:.2f}

🕐 Executed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
            
            await self.notification_layer.send_trade_alert(decision, additional_data={
                'fundamental_analysis': fundamental_analysis,
                'regime_analysis': regime_analysis,
                'trade_id': trade_id
            })
            
        except Exception as e:
            self.logger.error(f"Error sending enhanced trade notification: {e}")
    
    async def _send_enhanced_loop_report(self, loop_stats):
        """Send enhanced loop report with all component data."""
        try:
            # Get component summaries
            position_summary = await self.position_manager.get_position_summary()
            fundamental_summary = await self.fundamental_analyzer.get_fundamental_summary()
            risk_summary = await self.advanced_risk_manager.get_risk_summary()
            regime_summary = await self.market_regime_detector.get_regime_summary()
            
            loop_duration = (datetime.now() - loop_stats['start_time']).total_seconds()
            
            report_message = f"""
📊 ENHANCED LOOP REPORT - Loop #{loop_stats['loop_number']}
✅ Status: COMPLETED
⏱️ Duration: {loop_duration:.2f} seconds
🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 ANALYSIS SUMMARY:
• Pairs Analyzed: {len(loop_stats['pairs_analyzed'])} ({', '.join(loop_stats['pairs_analyzed'])})
• AI Analyses Performed: {loop_stats['ai_analyses_performed']}
• Recommendations Generated: {loop_stats['recommendations_generated']}
• Technical Indicators Calculated: {loop_stats['technical_indicators_calculated']}
• Data Points Processed: {loop_stats['data_points_processed']}
• Fundamental Analyses: {loop_stats['fundamental_analyses']}
• Regime Detections: {loop_stats['regime_detections']}
• Risk Assessments: {loop_stats['risk_assessments']}

🎯 TRADE DECISIONS:
• Trades Approved: {loop_stats['trades_approved']}
• Trades Rejected: {loop_stats['trades_rejected']}
• Approval Rate: {(loop_stats['trades_approved'] / max(1, loop_stats['trades_approved'] + loop_stats['trades_rejected'])) * 100:.1f}%

🌍 MARKET CONDITIONS OBSERVED:
{chr(10).join([f'• {condition}: {count} pairs' for condition, count in loop_stats['market_conditions_observed'].items()])}

🚀 ADVANCED COMPONENTS:
• Active Positions: {position_summary['active_positions']}
• Daily P&L: ${position_summary['daily_pnl']:.2f}
• Current Regime: {regime_summary['current_regime']} (Confidence: {regime_summary['regime_confidence']:.2f})
• Portfolio Heat: {risk_summary['portfolio_heat']:.2f}
• Win Rate: {risk_summary['win_rate']:.1%}
• Drawdown: {risk_summary['current_drawdown']:.2%}

📊 DAILY PERFORMANCE:
• Total Trades: {risk_summary['total_trades']}
• Winning Trades: {int(risk_summary['win_rate'] * risk_summary['total_trades'])}
• Losing Trades: {risk_summary['total_trades'] - int(risk_summary['win_rate'] * risk_summary['total_trades'])}
• Win Rate: {risk_summary['win_rate']:.1%}
• Profit Factor: {risk_summary['profit_factor']:.2f}
• Net Profit: ${position_summary['daily_pnl']:.2f}
""".strip()
            
            await self.notification_layer.send_notification(
                message=report_message,
                notification_type="LOOP_REPORT"
            )
            
        except Exception as e:
            self.logger.error(f"Error sending enhanced loop report: {e}")
    
    def _should_analyze_pair(self, pair: str) -> bool:
        """Check if we should analyze this pair."""
        return pair in self.config.trading_pairs
    
    async def cleanup(self):
        """Cleanup all components."""
        self.logger.info("Cleaning up trading bot...")
        self.is_running = False
        
        # Stop all components
        await self.data_layer.stop()
        await self.ai_layer.close()
        await self.decision_layer.close()
        await self.notification_layer.stop()
        
        # Stop new advanced components
        await self.position_manager.stop()
        await self.fundamental_analyzer.stop()
        await self.advanced_risk_manager.stop()
        await self.market_regime_detector.stop()
        
        self.logger.info("Trading bot cleanup completed")


async def main():
    """Main entry point."""
    bot = TradingBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print("\n🛑 Shutdown signal received. Cleaning up...")
        asyncio.create_task(bot.cleanup())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received.")
    except Exception as e:
        print(f"❌ Error in main: {e}")
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 