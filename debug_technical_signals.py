#!/usr/bin/env python3
"""
Debug script to check technical analysis signal generation.
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
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer


def load_debug_data() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load data for debugging."""
    
    print("📊 Loading debug data...")
    
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
                    
                    # Take the last 100 candles for debugging
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


async def debug_technical_analysis():
    """Debug the technical analysis layer."""
    
    print("🔍 Debugging Technical Analysis Layer")
    print("=" * 50)
    
    # Load configuration and data
    config = Config()
    historical_data = load_debug_data()
    
    if not historical_data:
        print("❌ No data available for debugging.")
        return
    
    # Get the data
    pair = "EUR_USD"
    timeframe = TimeFrame.M5
    candles = historical_data[pair][timeframe]
    
    print(f"📊 Analyzing {len(candles)} candles for {pair} {timeframe.value}")
    print(f"📅 Date range: {candles[0].timestamp} to {candles[-1].timestamp}")
    
    # Create technical analysis layer
    technical_layer = TechnicalAnalysisLayer(config)
    
    # Create market context
    market_context = MarketContext(
        condition=MarketCondition.RANGING,
        trend_strength=0.5,
        volatility=0.02,
        key_levels={},
        news_sentiment=0.0,
        economic_events=[]
    )
    
    # Test with different parameter sets
    test_params = [
        {
            'name': 'ULTRA LOOSE',
            'rsi_oversold': 50,
            'rsi_overbought': 50,
            'macd_signal_threshold': 0.00000001,
            'bollinger_threshold': 0.0001,
            'min_signal_strength': 0.01
        },
        {
            'name': 'NORMAL',
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_signal_threshold': 0.0001,
            'bollinger_threshold': 0.1,
            'min_signal_strength': 0.3
        }
    ]
    
    for param_set in test_params:
        print(f"\n🧪 Testing {param_set['name']} parameters:")
        print("-" * 30)
        
        # Apply parameters to AI analysis config
        config.ai_analysis.confidence_threshold = param_set['min_signal_strength']
        config.ai_analysis.signal_strength_threshold = param_set['bollinger_threshold']
        config.ai_analysis.minimum_confidence = param_set['min_signal_strength']
        
        # Test technical analysis
        try:
            recommendation, indicators = await technical_layer.analyze_multiple_timeframes(
                pair, {timeframe: candles}, market_context
            )
            
            print(f"   📊 Technical Analysis Result:")
            print(f"   - Recommendation: {recommendation}")
            print(f"   - Indicators calculated: {indicators is not None}")
            
            if recommendation:
                print(f"   ✅ SIGNAL GENERATED!")
                print(f"   - Signal: {recommendation.signal}")
                print(f"   - Confidence: {recommendation.confidence}")
                print(f"   - Entry Price: {recommendation.entry_price}")
                print(f"   - Stop Loss: {recommendation.stop_loss}")
                print(f"   - Take Profit: {recommendation.take_profit}")
            else:
                print(f"   ❌ NO SIGNAL GENERATED")
                
            if indicators:
                print(f"   📈 Indicators:")
                print(f"   - RSI: {indicators.rsi}")
                print(f"   - MACD: {indicators.macd}")
                print(f"   - MACD Signal: {indicators.macd_signal}")
                print(f"   - Bollinger Upper: {indicators.bollinger_upper}")
                print(f"   - Bollinger Lower: {indicators.bollinger_lower}")
                print(f"   - ATR: {indicators.atr}")
                
        except Exception as e:
            print(f"   ❌ Error in technical analysis: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG SUMMARY")
    print("=" * 50)
    print("If no signals are generated even with ultra-loose parameters,")
    print("the issue is likely in the technical analysis logic itself.")


async def main():
    """Main function."""
    try:
        await debug_technical_analysis()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
