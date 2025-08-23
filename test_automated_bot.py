#!/usr/bin/env python3
"""
Test script for the fully automated trading bot.
Tests the automated decision layer and notification system.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add trading_bot/src to the path
trading_bot_src = project_root / "trading_bot" / "src"
sys.path.append(str(trading_bot_src))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import (
    CandleData, MarketContext, MarketCondition, TradeRecommendation, 
    TradeSignal, TechnicalIndicators, TimeFrame, TradeDecision
)
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.decision.automated_decision_layer import AutomatedDecisionLayer
from trading_bot.src.notifications.notification_layer import NotificationLayer
from trading_bot.src.core.position_manager import PositionManager
from decimal import Decimal
from datetime import datetime, timezone


async def test_automated_bot():
    """Test the automated trading bot components."""
    print("🤖 Testing Automated Trading Bot Components")
    print("=" * 50)
    
    try:
        # Initialize configuration
        print("📋 Loading configuration...")
        config = Config()
        print(f"✅ Configuration loaded - Trading pairs: {config.trading_pairs}")
        
        # Initialize components
        print("\n🔧 Initializing components...")
        
        # Initialize notification layer (for testing)
        notification_layer = NotificationLayer(config)
        print("✅ Notification layer initialized")
        
        # Initialize position manager (mock for testing)
        position_manager = PositionManager(config, None)  # No OANDA API for testing
        print("✅ Position manager initialized")
        
        # Initialize automated decision layer
        decision_layer = AutomatedDecisionLayer(
            config, 
            notification_layer=notification_layer,
            position_manager=position_manager
        )
        print("✅ Automated decision layer initialized")
        
        # Initialize technical analysis layer
        technical_layer = TechnicalAnalysisLayer(config)
        print("✅ Technical analysis layer initialized")
        
        # Start components
        print("\n🚀 Starting components...")
        await notification_layer.start()
        await decision_layer.start()
        await technical_layer.start()
        print("✅ All components started")
        
        # Create test data
        print("\n📊 Creating test data...")
        
        # Create sample candles
        candles = []
        base_price = 1.2000
        for i in range(100):
            candle = CandleData(
                timestamp=datetime.now(timezone.utc),
                open=Decimal(str(base_price + i * 0.0001)),
                high=Decimal(str(base_price + i * 0.0001 + 0.0002)),
                low=Decimal(str(base_price + i * 0.0001 - 0.0001)),
                close=Decimal(str(base_price + i * 0.0001 + 0.0001)),
                volume=1000
            )
            candles.append(candle)
        
        # Create market context
        market_context = MarketContext(
            condition=MarketCondition.BREAKOUT,
            volatility=0.02,
            trend_strength=0.7,
            news_sentiment="POSITIVE"
        )
        
        # Create technical indicators
        indicators = TechnicalIndicators(
            rsi=65.0,
            macd=0.001,
            macd_signal=0.0005,
            macd_histogram=0.0005,
            atr=0.002,
            ema_fast=1.2005,
            ema_slow=1.2000,
            bollinger_upper=1.2010,
            bollinger_middle=1.2005,
            bollinger_lower=1.2000,
            keltner_upper=1.2012,
            keltner_middle=1.2005,
            keltner_lower=1.1998
        )
        
        # Create trade recommendation
        recommendation = TradeRecommendation(
            id="test_001",
            pair="EUR_USD",
            signal=TradeSignal.BUY,
            confidence=0.85,
            entry_price=Decimal("1.2005"),
            stop_loss=Decimal("1.1995"),
            take_profit=Decimal("1.2020"),
            risk_reward_ratio=1.5,
            market_condition=MarketCondition.BREAKOUT,
            estimated_hold_time="2 hours",
            reasoning="Strong bullish momentum with RSI above 50 and MACD positive. Price breaking above resistance with good volume support.",
            timestamp=datetime.now(timezone.utc)
        )
        
        print("✅ Test data created")
        
        # Test automated decision processing
        print("\n🎯 Testing automated decision processing...")
        
        current_price = Decimal("1.2005")
        
        # Process recommendation through automated decision layer
        decision = await decision_layer.process_recommendation(
            recommendation=recommendation,
            current_price=current_price,
            market_context=market_context,
            technical_indicators={TimeFrame.M5: indicators},
            candles_by_timeframe={TimeFrame.M5: candles},
            ai_outputs={'test': 'data'},
            multi_timeframe_analysis={'test': 'analysis'},
            risk_assessment=None,
            raw_data={'test': 'raw_data'}
        )
        
        if decision:
            print(f"✅ Decision processed successfully!")
            print(f"   - Approved: {decision.approved}")
            print(f"   - Position Size: {decision.position_size}")
            print(f"   - Risk Amount: ${decision.risk_amount}")
            print(f"   - Stop Loss: {decision.modified_stop_loss}")
            print(f"   - Take Profit: {decision.modified_take_profit}")
            print(f"   - Risk Notes: {decision.risk_management_notes}")
        else:
            print("❌ Decision processing failed or was rejected")
        
        # Test position status updates
        print("\n📈 Testing position status updates...")
        
        if decision and decision.approved:
            # Simulate position opening
            await decision_layer.update_position_status(
                pair="EUR_USD",
                status="opened",
                execution_price=current_price
            )
            print("✅ Position opened notification sent")
            
            # Simulate position closing
            exit_price = Decimal("1.2015")
            await decision_layer.update_position_status(
                pair="EUR_USD",
                status="closed",
                execution_price=exit_price,
                exit_reason="Take profit reached"
            )
            print("✅ Position closed notification sent")
        
        # Test error handling
        print("\n🚨 Testing error handling...")
        
        # Create a recommendation with low confidence
        low_confidence_recommendation = TradeRecommendation(
            id="test_002",
            pair="GBP_USD",
            signal=TradeSignal.SELL,
            confidence=0.3,  # Below threshold
            entry_price=Decimal("1.3000"),
            stop_loss=Decimal("1.3010"),
            take_profit=Decimal("1.2980"),
            risk_reward_ratio=1.0,
            market_condition=MarketCondition.RANGING,
            estimated_hold_time="1 hour",
            reasoning="Weak signal with low confidence.",
            timestamp=datetime.now(timezone.utc)
        )
        
        decision2 = await decision_layer.process_recommendation(
            recommendation=low_confidence_recommendation,
            current_price=Decimal("1.3000"),
            market_context=market_context,
            technical_indicators={TimeFrame.M5: indicators},
            candles_by_timeframe={TimeFrame.M5: candles},
            ai_outputs={},
            multi_timeframe_analysis={},
            risk_assessment=None,
            raw_data={}
        )
        
        if not decision2:
            print("✅ Low confidence recommendation correctly rejected")
        else:
            print("⚠️ Low confidence recommendation was processed (unexpected)")
        
        # Get execution history
        print("\n📊 Getting execution history...")
        execution_history = await decision_layer.get_execution_history()
        print(f"✅ Execution history: {len(execution_history)} records")
        
        # Get open positions
        print("\n📋 Getting open positions...")
        open_positions = await decision_layer.get_open_positions()
        print(f"✅ Open positions: {len(open_positions)} positions")
        
        # Clean up
        print("\n🧹 Cleaning up...")
        await decision_layer.close()
        await notification_layer.close()
        # Technical analysis layer doesn't have a close method
        print("✅ Cleanup completed")
        
        print("\n🎉 Automated bot test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_automated_bot())
    sys.exit(0 if success else 1)
