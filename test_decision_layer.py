#!/usr/bin/env python3
"""
Test script to check the decision layer.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition, TradeRecommendation, TradeSignal
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
from trading_bot.src.decision.technical_decision_layer import TechnicalDecisionLayer


def load_test_data() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load test data."""
    
    print("📊 Loading test data...")
    
    # Load EUR_USD M5 data
    historical_data = {}
    pairs = ["EUR_USD"]
    timeframes = [TimeFrame.M5]
    
    for pair in pairs:
        historical_data[pair] = {}
        
        for timeframe in timeframes:
            try:
                file_path = f"data/{pair}_{timeframe.value}.pkl"
                if os.path.exists(file_path):
                    df = pd.read_pickle(file_path)
                    
                    # Take the last 100 candles
                    df = df.tail(100)
                    
                    candles = []
                    for _, row in df.iterrows():
                        timestamp = row["time"].to_pydatetime()
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                        
                        candle = CandleData(
                            timestamp=timestamp,
                            open=Decimal(str(row["mid_o"])),
                            high=Decimal(str(row["mid_h"])),
                            low=Decimal(str(row["mid_l"])),
                            close=Decimal(str(row["mid_c"])),
                            volume=Decimal(str(row.get("volume", 1000)))
                        )
                        candles.append(candle)
                    
                    historical_data[pair][timeframe] = candles
                    print(f"   ✅ Loaded {len(candles)} candles for {pair} {timeframe.value}")
                    
                else:
                    print(f"   ❌ File not found: {file_path}")
                    return {}
                    
            except Exception as e:
                print(f"   ❌ Error loading data: {e}")
                return {}
    
    return historical_data


async def test_decision_layer():
    """Test the decision layer."""
    
    print("🔍 Testing Decision Layer")
    print("=" * 50)
    
    # Load configuration and data
    config = Config()
    historical_data = load_test_data()
    
    if not historical_data:
        print("❌ No data available for testing.")
        return
    
    # Get the data
    pair = "EUR_USD"
    timeframe = TimeFrame.M5
    candles = historical_data[pair][timeframe]
    
    print(f"📊 Testing with {len(candles)} candles for {pair} {timeframe.value}")
    
    # Create layers
    technical_layer = TechnicalAnalysisLayer(config)
    decision_layer = TechnicalDecisionLayer(config)
    
    # Create market context
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        trend_strength=0.5,
        volatility=0.02,
        key_levels={},
        news_sentiment=0.0,
        economic_events=[]
    )
    
    # Test with ultra-loose parameters
    config.ai_analysis.confidence_threshold = 0.01
    config.ai_analysis.signal_strength_threshold = 0.0001
    config.ai_analysis.minimum_confidence = 0.01
    
    print("\n🧪 Step 1: Technical Analysis")
    print("-" * 30)
    
    try:
        # Get technical recommendation
        recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
            pair, {timeframe: candles}, market_context
        )
        
        if recommendation:
            print(f"   ✅ Technical Analysis SUCCESS")
            print(f"   - Signal: {recommendation.signal}")
            print(f"   - Confidence: {recommendation.confidence}")
            print(f"   - Entry Price: {recommendation.entry_price}")
            print(f"   - Stop Loss: {recommendation.stop_loss}")
            print(f"   - Take Profit: {recommendation.take_profit}")
        else:
            print(f"   ❌ Technical Analysis FAILED - No recommendation")
            return
            
    except Exception as e:
        print(f"   ❌ Technical Analysis ERROR: {e}")
        return
    
    print("\n🧪 Step 2: Decision Layer")
    print("-" * 30)
    
    try:
        # Get current price
        current_price = candles[-1].close
        
        # Make decision
        decision = await decision_layer.make_technical_decision(
            pair, {timeframe: indicators}, market_context, current_price, {timeframe: candles}
        )
        
        if decision:
            print(f"   ✅ Decision Layer SUCCESS")
            print(f"   - Approved: {decision.approved}")
            print(f"   - Position Size: {decision.position_size}")
            print(f"   - Risk Amount: {decision.risk_amount}")
            print(f"   - Modified Stop Loss: {decision.modified_stop_loss}")
            print(f"   - Modified Take Profit: {decision.modified_take_profit}")
            print(f"   - Risk Notes: {decision.risk_management_notes}")
            
            if decision.approved:
                print(f"   🎉 TRADE APPROVED!")
            else:
                print(f"   ❌ TRADE REJECTED")
                print(f"   📝 Reason: {decision.risk_management_notes}")
        else:
            print(f"   ❌ Decision Layer FAILED - No decision")
            
    except Exception as e:
        print(f"   ❌ Decision Layer ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 DECISION LAYER TEST SUMMARY")
    print("=" * 50)


async def main():
    """Main function."""
    try:
        await test_decision_layer()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
