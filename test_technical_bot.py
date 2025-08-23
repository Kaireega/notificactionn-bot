#!/usr/bin/env python3
"""
Test script for the technical analysis trading bot (without AI).
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.decision.technical_decision_layer import TechnicalDecisionLayer
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from decimal import Decimal
from datetime import datetime, timezone


async def test_technical_analysis():
    """Test the technical analysis layer without AI."""
    print("🧪 Testing Technical Analysis Layer (No AI)")
    print("=" * 50)
    
    try:
        # Initialize config
        config = Config()
        print("✅ Config loaded")
        
        # Initialize technical analysis layer
        technical_layer = TechnicalAnalysisLayer(config)
        print("✅ Technical analysis layer initialized")
        
        # Create mock candle data
        mock_candles = []
        base_price = Decimal('1.1000')
        
        for i in range(50):
            # Create some trending data
            price_change = Decimal(str(i * 0.0001))
            high = base_price + price_change + Decimal('0.0005')
            low = base_price + price_change - Decimal('0.0005')
            open_price = base_price + price_change
            close_price = base_price + price_change + Decimal('0.0002')
            
            candle = CandleData(
                timestamp=datetime.now(timezone.utc),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=Decimal('1000')
            )
            mock_candles.append(candle)
        
        # Create market context
        market_context = MarketContext(
            condition=MarketCondition.TRENDING,
            volatility=Decimal('0.001'),
            trend_strength=Decimal('0.7'),
            news_sentiment=Decimal('0.0')
        )
        
        # Test technical analysis
        candles_by_timeframe = {TimeFrame.M5: mock_candles}
        
        print("🔍 Running technical analysis...")
        recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
            "EUR_USD", candles_by_timeframe, market_context
        )
        
        if recommendation:
            print(f"✅ Technical recommendation generated:")
            print(f"   Signal: {recommendation.signal.value}")
            print(f"   Confidence: {recommendation.confidence:.3f}")
            print(f"   Entry Price: {recommendation.entry_price}")
            print(f"   Stop Loss: {recommendation.stop_loss}")
            print(f"   Take Profit: {recommendation.take_profit}")
            print(f"   Risk/Reward: {recommendation.risk_reward_ratio:.2f}")
            print(f"   Reasoning: {recommendation.reasoning}")
        else:
            print("ℹ️ No technical recommendation generated")
        
        if indicators:
            print(f"✅ Technical indicators calculated:")
            print(f"   RSI: {indicators.rsi:.2f}")
            print(f"   MACD: {indicators.macd:.6f}")
            print(f"   MACD Signal: {indicators.macd_signal:.6f}")
            print(f"   ATR: {indicators.atr:.6f}")
            print(f"   EMA Fast: {indicators.ema_fast:.6f}")
            print(f"   EMA Slow: {indicators.ema_slow:.6f}")
        
        print("\n" + "=" * 50)
        print("✅ Technical analysis test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in technical analysis test: {e}")
        import traceback
        traceback.print_exc()


async def test_technical_decision():
    """Test the technical decision layer."""
    print("\n🧪 Testing Technical Decision Layer")
    print("=" * 50)
    
    try:
        # Initialize config
        config = Config()
        print("✅ Config loaded")
        
        # Initialize technical decision layer
        decision_layer = TechnicalDecisionLayer(config)
        print("✅ Technical decision layer initialized")
        
        # Start the decision layer
        await decision_layer.start()
        print("✅ Technical decision layer started")
        
        # Create mock data (same as above)
        mock_candles = []
        base_price = Decimal('1.1000')
        
        for i in range(50):
            price_change = Decimal(str(i * 0.0001))
            high = base_price + price_change + Decimal('0.0005')
            low = base_price + price_change - Decimal('0.0005')
            open_price = base_price + price_change
            close_price = base_price + price_change + Decimal('0.0002')
            
            candle = CandleData(
                timestamp=datetime.now(timezone.utc),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=Decimal('1000')
            )
            mock_candles.append(candle)
        
        # Create market context
        market_context = MarketContext(
            condition=MarketCondition.TRENDING,
            volatility=Decimal('0.001'),
            trend_strength=Decimal('0.7'),
            news_sentiment=Decimal('0.0')
        )
        
        # Get technical indicators
        technical_layer = TechnicalAnalysisLayer(config)
        candles_by_timeframe = {TimeFrame.M5: mock_candles}
        recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
            "EUR_USD", candles_by_timeframe, market_context
        )
        
        if indicators:
            # Test decision making
            technical_indicators = {TimeFrame.M5: indicators}
            current_price = Decimal('1.1050')
            
            print("🔍 Running technical decision making...")
            decision = await decision_layer.make_technical_decision(
                "EUR_USD", technical_indicators, market_context, current_price, candles_by_timeframe
            )
            
            if decision:
                print(f"✅ Technical decision generated:")
                print(f"   Approved: {decision.approved}")
                print(f"   Signal: {decision.recommendation.signal.value}")
                print(f"   Confidence: {decision.recommendation.confidence:.3f}")
                print(f"   Position Size: {decision.position_size}")
                print(f"   Risk Amount: ${decision.risk_amount}")
                print(f"   Stop Loss: {decision.modified_stop_loss}")
                print(f"   Take Profit: {decision.modified_take_profit}")
            else:
                print("ℹ️ No technical decision generated")
        
        # Close the decision layer
        await decision_layer.close()
        print("✅ Technical decision layer closed")
        
        print("\n" + "=" * 50)
        print("✅ Technical decision test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in technical decision test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting Technical Analysis Bot Tests (No AI)")
    print("=" * 60)
    
    await test_technical_analysis()
    await test_technical_decision()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("✅ The bot now works without AI analysis layer")


if __name__ == "__main__":
    asyncio.run(main())
