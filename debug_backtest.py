#!/usr/bin/env python3
"""
Debug script to test backtesting components step by step.
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
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer


def load_sample_data() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load a small sample of historical data for debugging."""
    
    print("📊 Loading sample data for debugging...")
    
    # Load just EUR_USD M5 data for a short period
    file_path = "data/EUR_USD_M5.pkl"
    df = pd.read_pickle(file_path)
    
    # Take last 1000 candles
    df_sample = df.tail(1000)
    
    # Convert to CandleData objects
    candles = []
    for _, row in df_sample.iterrows():
        candle = CandleData(
            timestamp=row["time"].to_pydatetime(),
            open=Decimal(str(row["mid_o"])),
            high=Decimal(str(row["mid_h"])),
            low=Decimal(str(row["mid_l"])),
            close=Decimal(str(row["mid_c"])),
            volume=Decimal(str(row.get("volume", 1000)))
        )
        candles.append(candle)
    
    print(f"   ✅ Loaded {len(candles)} sample candles")
    
    # Create historical data structure
    historical_data = {
        "EUR_USD": {
            TimeFrame.M5: candles
        }
    }
    
    return historical_data


async def test_technical_analysis():
    """Test the technical analysis layer."""
    
    print("🔧 Testing Technical Analysis Layer...")
    
    # Load configuration
    config = Config()
    
    # Initialize technical analysis layer
    technical_layer = TechnicalAnalysisLayer(config)
    await technical_layer.start()
    
    # Load sample data
    historical_data = load_sample_data()
    
    # Test with one pair
    pair = "EUR_USD"
    timeframes = historical_data[pair]
    
    # Create market context
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        volatility=Decimal('0.001'),
        trend_strength=Decimal('0.0'),
        news_sentiment=Decimal('0.0')
    )
    
    print(f"📊 Testing technical analysis for {pair}...")
    print(f"   Timeframes available: {list(timeframes.keys())}")
    print(f"   M5 candles: {len(timeframes[TimeFrame.M5])}")
    
    # Run technical analysis
    try:
        recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
            pair, timeframes, market_context
        )
        
        print(f"   ✅ Technical analysis completed")
        print(f"   📊 Recommendation: {recommendation}")
        print(f"   📈 Indicators: {indicators}")
        
        if recommendation:
            print(f"   🎯 Signal: {recommendation.signal}")
            print(f"   📊 Confidence: {recommendation.confidence}")
            print(f"   💰 Entry Price: {recommendation.entry_price}")
            print(f"   🛑 Stop Loss: {recommendation.stop_loss}")
            print(f"   🎯 Take Profit: {recommendation.take_profit}")
        
        if indicators:
            print(f"   📊 RSI: {indicators.rsi}")
            print(f"   📊 MACD: {indicators.macd}")
            print(f"   📊 ATR: {indicators.atr}")
        
    except Exception as e:
        print(f"   ❌ Error in technical analysis: {e}")
        import traceback
        traceback.print_exc()
    
    await technical_layer.stop()


async def main():
    """Main function."""
    try:
        await test_technical_analysis()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
