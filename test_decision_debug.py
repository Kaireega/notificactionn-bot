#!/usr/bin/env python3
"""
Debug the decision layer to see why trades are being rejected.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer


def create_test_data():
    """Create test data."""
    candles = []
    base_price = 1.1000
    
    for i in range(50):
        if i < 25:
            price_change = -0.003 - (i * 0.0003)
        else:
            price_change = 0.003 + ((i - 25) * 0.0003)
        
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(50-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.001)),
            low=Decimal(str(current_price - 0.001)),
            close=Decimal(str(current_price + price_change * 0.3)),
            volume=Decimal('1000')
        )
        candles.append(candle)
    
    return candles


async def test_decision_debug():
    """Test decision layer debugging."""
    
    print("🔧 Testing Decision Layer Debugging...")
    
    # Load configuration
    config = Config()
    
    # Create test data
    candles = create_test_data()
    print(f"   ✅ Created {len(candles)} test candles")
    
    # Initialize technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    # Calculate indicators
    indicators = technical_analyzer.calculate_indicators(candles)
    print(f"   ✅ Technical indicators calculated")
    print(f"   📊 RSI: {indicators.rsi}")
    print(f"   📊 MACD: {indicators.macd}")
    print(f"   📊 ATR: {indicators.atr}")
    
    # Test technical analysis layer
    from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
    technical_layer = TechnicalAnalysisLayer(config)
    
    # Apply very lenient parameters
    technical_layer.rsi_oversold = 45
    technical_layer.rsi_overbought = 55
    technical_layer.macd_signal_threshold = 0.000001
    technical_layer.bollinger_threshold = 0.005
    technical_layer.min_signal_strength = 0.1
    
    # Create market context
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        volatility=Decimal('0.001'),
        trend_strength=Decimal('0.0'),
        news_sentiment=Decimal('0.0')
    )
    
    # Create timeframes data
    timeframes = {TimeFrame.M5: candles}
    
    # Get current price
    current_price = technical_layer._get_current_price(candles)
    print(f"   📊 Current price: {current_price}")
    
    # Run technical analysis
    try:
        recommendation, indicators_result = await technical_layer.analyze_multiple_timeframes(
            "EUR_USD", timeframes, market_context
        )
        
        print(f"   ✅ Technical analysis completed")
        print(f"   📊 Recommendation: {recommendation}")
        
        if recommendation:
            print(f"   🎯 Signal: {recommendation.signal}")
            print(f"   📊 Confidence: {recommendation.confidence}")
            print(f"   💰 Entry Price: {recommendation.entry_price}")
            print(f"   🛑 Stop Loss: {recommendation.stop_loss}")
            print(f"   🎯 Take Profit: {recommendation.take_profit}")
            
            # Test decision layer with detailed debugging
            from trading_bot.src.decision.technical_decision_layer import TechnicalDecisionLayer
            decision_layer = TechnicalDecisionLayer(config)
            
            # Check confidence threshold
            print(f"\n🔧 Decision Layer Debugging:")
            print(f"   📊 AI confidence threshold: {config.ai_confidence_threshold}")
            print(f"   📊 Recommendation confidence: {recommendation.confidence}")
            print(f"   📊 Confidence check: {recommendation.confidence >= config.ai_confidence_threshold}")
            
            # Make decision
            decision = await decision_layer.make_technical_decision(
                "EUR_USD", {TimeFrame.M5: indicators_result}, market_context, current_price, timeframes
            )
            
            print(f"   ✅ Decision layer completed")
            print(f"   📊 Decision: {decision}")
            
            if decision:
                print(f"   🎯 Approved: {decision.approved}")
                print(f"   📊 Risk Management Notes: {decision.risk_management_notes}")
                print(f"   💰 Modified Stop Loss: {decision.modified_stop_loss}")
                print(f"   🎯 Modified Take Profit: {decision.modified_take_profit}")
            else:
                print(f"   ❌ No decision generated")
        else:
            print(f"   ❌ No recommendation generated")
        
    except Exception as e:
        print(f"   ❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function."""
    try:
        await test_decision_debug()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
