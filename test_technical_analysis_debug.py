#!/usr/bin/env python3
"""
Debug test for technical analysis layer.
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


def create_test_candles():
    """Create test candles."""
    candles = []
    base_price = 1.1000
    
    for i in range(50):
        price_change = (i % 10 - 5) * 0.0001
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=datetime.now() - timedelta(minutes=(50-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.0002)),
            low=Decimal(str(current_price - 0.0002)),
            close=Decimal(str(current_price + price_change * 0.1)),
            volume=Decimal('1000')
        )
        candles.append(candle)
    
    return candles


async def test_technical_analysis_step_by_step():
    """Test technical analysis step by step."""
    print("�� Testing Technical Analysis Step by Step...")
    
    # Create test candles
    candles = create_test_candles()
    print(f"   ✅ Created {len(candles)} test candles")
    
    # Initialize technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    # Test step 1: Convert candles to DataFrame
    try:
        print(f"   🔧 Step 1: Converting candles to DataFrame...")
        df = technical_analyzer._candles_to_dataframe(candles)
        print(f"   ✅ DataFrame conversion successful: {df.shape}")
    except Exception as e:
        print(f"   ❌ Error in DataFrame conversion: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test step 2: Calculate indicators
    try:
        print(f"   🔧 Step 2: Calculating technical indicators...")
        indicators = technical_analyzer.calculate_indicators(candles)
        print(f"   ✅ Technical indicators calculated successfully")
        print(f"   📊 RSI: {indicators.rsi}")
        print(f"   📊 MACD: {indicators.macd}")
        print(f"   📊 ATR: {indicators.atr}")
    except Exception as e:
        print(f"   ❌ Error calculating indicators: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test step 3: Analyze signals
    try:
        print(f"   🔧 Step 3: Analyzing signals...")
        from trading_bot.src.ai.technical_analysis_layer import TechnicalAnalysisLayer
        
        # Initialize technical analysis layer
        config = Config()
        technical_layer = TechnicalAnalysisLayer(config)
        
        # Create market context
        market_context = MarketContext(
            condition=MarketCondition.RANGING,
            volatility=Decimal('0.001'),
            trend_strength=Decimal('0.0'),
            news_sentiment=Decimal('0.0')
        )
        
        # Create timeframes data
        timeframes = {TimeFrame.M5: candles}
        
        # Analyze signals
        signal_analysis = technical_layer._analyze_technical_signals(indicators, market_context)
        print(f"   ✅ Signal analysis completed")
        print(f"   📊 Has signal: {signal_analysis['has_signal']}")
        print(f"   📊 Overall signal: {signal_analysis['overall_signal']}")
        print(f"   📊 Signal strength: {signal_analysis['signal_strength']}")
        print(f"   📊 Reasoning: {signal_analysis['reasoning']}")
        
    except Exception as e:
        print(f"   ❌ Error in signal analysis: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function."""
    try:
        await test_technical_analysis_step_by_step()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
