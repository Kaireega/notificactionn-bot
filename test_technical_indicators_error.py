#!/usr/bin/env python3
"""
Test to isolate the decimal/float error in technical indicators.
"""
import sys
import os
from pathlib import Path
from decimal import Decimal
import pandas as pd

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.core.models import CandleData


def create_test_candles():
    """Create test candles."""
    candles = []
    base_price = 1.1000
    
    for i in range(50):
        price_change = (i % 10 - 5) * 0.0001
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=pd.Timestamp.now() - pd.Timedelta(minutes=(50-i)*5),
            open=Decimal(str(current_price)),
            high=Decimal(str(current_price + 0.0002)),
            low=Decimal(str(current_price - 0.0002)),
            close=Decimal(str(current_price + price_change * 0.1)),
            volume=Decimal('1000')
        )
        candles.append(candle)
    
    return candles


def test_technical_indicators():
    """Test technical indicators directly."""
    print("🔧 Testing Technical Indicators...")
    
    # Create test candles
    candles = create_test_candles()
    print(f"   ✅ Created {len(candles)} test candles")
    
    # Convert to DataFrame
    data = []
    for candle in candles:
        data.append({
            'mid_o': float(candle.open),
            'mid_h': float(candle.high),
            'mid_l': float(candle.low),
            'mid_c': float(candle.close),
            'volume': float(candle.volume) if candle.volume else 0
        })
    
    df = pd.DataFrame(data)
    print(f"   ✅ Converted to DataFrame with shape: {df.shape}")
    
    # Test each indicator individually
    try:
        from technicals.indicators import RSI
        print(f"   🔧 Testing RSI...")
        df_rsi = RSI(df, n=14)
        print(f"   ✅ RSI calculated successfully")
    except Exception as e:
        print(f"   ❌ Error in RSI: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from technicals.indicators import MACD
        print(f"   🔧 Testing MACD...")
        df_macd = MACD(df, n_slow=26, n_fast=12, n_signal=9)
        print(f"   ✅ MACD calculated successfully")
    except Exception as e:
        print(f"   ❌ Error in MACD: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from technicals.indicators import BollingerBands
        print(f"   🔧 Testing Bollinger Bands...")
        df_bb = BollingerBands(df, n=20, s=2)
        print(f"   ✅ Bollinger Bands calculated successfully")
    except Exception as e:
        print(f"   ❌ Error in Bollinger Bands: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from technicals.indicators import ATR
        print(f"   🔧 Testing ATR...")
        df_atr = ATR(df, n=14)
        print(f"   ✅ ATR calculated successfully")
    except Exception as e:
        print(f"   ❌ Error in ATR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_technical_indicators()
