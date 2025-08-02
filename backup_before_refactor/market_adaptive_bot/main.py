#!/usr/bin/env python3
"""
Market Adaptive Trading Bot - Main Entry Point
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.config import Config
from data.data_layer import DataLayer
from ai.ai_analysis_layer import AIAnalysisLayer
from decision.decision_layer import DecisionLayer
from notifications.notification_layer import NotificationLayer
from core.models import TimeFrame, TechnicalIndicators

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot class that orchestrates all components."""
    
    def __init__(self):
        """Initialize the trading bot with all components."""
        try:
            # Load configuration
            self.config = Config()
            logger.info("Configuration loaded successfully")
            
            # Initialize components
            self.data_layer = DataLayer(self.config)
            self.ai_layer = AIAnalysisLayer(self.config)
            self.decision_layer = DecisionLayer(self.config)
            self.notification_layer = NotificationLayer(self.config)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading bot: {e}")
            raise
    
    async def start(self):
        """Start the trading bot."""
        try:
            logger.info("Starting Market Adaptive Trading Bot...")
            
            # Start all components
            await self.data_layer.start()
            logger.info("Data layer started")
            
            await self.ai_layer.start()
            logger.info("AI analysis layer started")
            
            await self.decision_layer.start()
            logger.info("Decision layer started")
            
            await self.notification_layer.start()
            logger.info("Notification layer started")
            
            logger.info("Trading bot is now running!")
            
            # Send startup notification
            await self._send_startup_message()
            
            # Start the trading loop
            await self._trading_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    async def _send_startup_message(self):
        """Send a startup notification message with performance summary."""
        try:
            # Get timeframes as strings
            timeframes = [tf.value for tf in self.config.timeframes]

            # Get current performance metrics (all-time)
            performance_metrics = await self.decision_layer.get_daily_performance()
            perf = performance_metrics  # for brevity

            perf_summary = (
                f"\nPerformance Summary:\n"
                f"• Total Trades: {perf.total_trades}\n"
                f"• Winning Trades: {perf.winning_trades}\n"
                f"• Losing Trades: {perf.losing_trades}\n"
                f"• Win Rate: {perf.win_rate:.1%}\n"
                f"• Net Profit: {perf.net_profit:.2f}\n"
                f"• Profit Factor: {perf.profit_factor:.2f}\n"
                f"• Max Drawdown: {perf.max_drawdown:.2f}\n"
                f"• Sharpe Ratio: {perf.sharpe_ratio:.2f}\n"
            )

            startup_message = f"""
🤖 Trading Bot Started Successfully

Configuration:
• Trading Pairs: {', '.join(self.config.trading_pairs)}
• Multi-timeframe Analysis: {', '.join(timeframes)}
• Risk Management: {self.config.trading.risk_percentage}% per trade
• Daily Loss Limit: {self.config.risk_management.max_daily_loss}%

Components Status:
✅ Data Layer: Active
✅ AI Analysis: Active  
✅ Decision Layer: Active
✅ Notifications: Active

{perf_summary}
Bot is now monitoring markets and ready for trading signals.

Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

            # Send to all notification channels (with error handling)
            if self.notification_layer:
                try:
                    await self.notification_layer.send_notification(
                        message=startup_message,
                        notification_type="STARTUP"
                    )
                    logger.info("Startup notification sent successfully")
                except Exception as e:
                    logger.warning(f"Startup notification failed (bot will continue): {e}")
                    logger.info("Bot is running without notifications - check your Telegram/Email setup")
            else:
                logger.info("No notification layer available - bot running without notifications")
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
            logger.info("Bot will continue running without startup notification")
    
    async def _trading_loop(self):
        """Main trading loop with multi-timeframe analysis."""
        while True:
            try:
                # Get data for all pairs
                all_data = await self.data_layer.get_all_pairs_data()
                
                for pair, data in all_data.items():
                    # Check if we should analyze this pair
                    if self._should_analyze_pair(pair):
                        # Get candles for all timeframes
                        candles_by_timeframe = {}
                        for timeframe in self.config.timeframes:
                            candles = await self.data_layer.get_candles(pair, timeframe, 100)
                            if candles:
                                candles_by_timeframe[timeframe] = candles
                        
                        if len(candles_by_timeframe) >= 2:  # Need at least 2 timeframes
                            # Get market context
                            market_context = data['market_context']
                            
                            # Perform multi-timeframe analysis (this already calculates technical indicators)
                            recommendation, technical_indicators = await self.ai_layer.analyze_multiple_timeframes(
                                pair, candles_by_timeframe, market_context
                            )
                            
                            if recommendation and recommendation.confidence > 0.6:
                                # Get current price
                                current_price = data['current_price']
                                if current_price:
                                    # Use the technical indicators that were already calculated by the AI layer
                                    
                                    # Prepare AI outputs data
                                    ai_outputs = {
                                        "prompt": "Multi-timeframe analysis prompt",
                                        "raw_response": str(recommendation),
                                        "parsed_data": {
                                            "signal": recommendation.signal.value,
                                            "confidence": recommendation.confidence,
                                            "entry_price": float(recommendation.entry_price) if recommendation.entry_price else None,
                                            "stop_loss": float(recommendation.stop_loss) if recommendation.stop_loss else None,
                                            "take_profit": float(recommendation.take_profit) if recommendation.take_profit else None,
                                            "reasoning": recommendation.reasoning,
                                            "market_condition": recommendation.market_condition.value,
                                            "risk_reward_ratio": recommendation.risk_reward_ratio,
                                            "estimated_hold_time_minutes": recommendation.estimated_hold_time.total_seconds() / 60 if recommendation.estimated_hold_time else None
                                        },
                                        "confidence": recommendation.confidence,
                                        "signal": recommendation.signal.value,
                                        "reasoning": recommendation.reasoning,
                                        "market_condition": recommendation.market_condition.value,
                                        "entry_price": recommendation.entry_price,
                                        "stop_loss": recommendation.stop_loss,
                                        "take_profit": recommendation.take_profit,
                                        "risk_reward_ratio": recommendation.risk_reward_ratio,
                                        "estimated_hold_time_minutes": recommendation.estimated_hold_time.total_seconds() / 60 if recommendation.estimated_hold_time else None,
                                        "model": "gpt-4",
                                        "temperature": 0.3,
                                        "max_tokens": 1000
                                    }
                                    
                                    # Prepare multi-timeframe analysis data
                                    multi_timeframe_analysis = {}
                                    for timeframe, candles in candles_by_timeframe.items():
                                        if candles:
                                            multi_timeframe_analysis[timeframe] = {
                                                "signal_type": recommendation.signal.value,
                                                "signal_strength": recommendation.confidence,
                                                "trend_direction": 0.0,  # Placeholder
                                                "momentum": 0.0,  # Placeholder
                                                "volatility": 0.0,  # Placeholder
                                                "technical_score": recommendation.confidence,
                                                "entry_price": recommendation.entry_price,
                                                "stop_loss": recommendation.stop_loss,
                                                "take_profit": recommendation.take_profit,
                                                "risk_reward_ratio": recommendation.risk_reward_ratio,
                                                "confidence": recommendation.confidence,
                                                "weight": 0.25  # Equal weight for each timeframe
                                            }
                                    
                                    # Prepare raw data
                                    raw_data = {
                                        "timeframe": "M5",
                                        "candle_count": len(candles_by_timeframe.get(TimeFrame.M5, [])),
                                        "price_data": [float(c.close) for c in candles_by_timeframe.get(TimeFrame.M5, [])],
                                        "volume_data": [float(c.volume) if c.volume else 0 for c in candles_by_timeframe.get(TimeFrame.M5, [])],
                                        "market_context_raw": market_context.__dict__,
                                        "technical_analysis_raw": {},
                                        "news_data": [],
                                        "economic_data": [],
                                        "sentiment_data": {}
                                    }
                                    
                                    # Process recommendation through decision layer with ALL data
                                    decision = await self.decision_layer.process_recommendation(
                                        recommendation, current_price, market_context,
                                        technical_indicators=technical_indicators,
                                        candles_by_timeframe=candles_by_timeframe,
                                        ai_outputs=ai_outputs,
                                        multi_timeframe_analysis=multi_timeframe_analysis,
                                        risk_assessment={},  # Will be filled by risk manager
                                        raw_data=raw_data
                                    )
                                    
                                    if decision and decision.approved:
                                        # Send notification
                                        await self.notification_layer.send_trade_alert(decision)
                                        logger.info(f"Trade alert sent for {pair}")
                
                # Wait before next analysis cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def _should_analyze_pair(self, pair: str) -> bool:
        """Check if we should analyze this pair."""
        # Add your logic here (e.g., market hours, pair preferences)
        return pair in self.config.trading_pairs
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.data_layer.stop()
            await self.ai_layer.stop()
            await self.decision_layer.stop()
            await self.notification_layer.stop()
            logger.info("Trading bot shutdown complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point."""
    try:
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # Create and start the trading bot
        bot = TradingBot()
        await bot.start()
        
    except Exception as e:
        logger.error(f"Failed to start trading bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 