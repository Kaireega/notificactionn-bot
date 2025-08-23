#!/usr/bin/env python3
"""
Simple test to check technical indicators functionality.
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

def create_sample_candles():
    """Create sample candle data for testing."""
    candles = []
    base_price = 1.1000
    
    for i in range(100):
        # Create simple price movement
        price_change = (i % 10 - 5) * 0.0001  # Oscillating price
        current_price = base_price + price_change
        
        candle = CandleData(
            timestamp=pd.Timestamp.now() - pd.Timedelta(minutes=(100-i)*5),
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
    
    # Create sample candles
    candles = create_sample_candles()
    print(f"   ✅ Created {len(candles)} sample candles")
    
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
    print(f"   📊 First few rows:")
    print(df.head())
    
    # Test RSI
    try:
        from technicals.indicators import RSI
        df_rsi = RSI(df, n=14)
        print(f"   ✅ RSI calculated successfully")
        print(f"   📊 RSI columns: {[col for col in df_rsi.columns if 'RSI' in col]}")
        if 'RSI_14' in df_rsi.columns:
            latest_rsi = df_rsi.iloc[-1]['RSI_14']
            print(f"   📊 Latest RSI: {latest_rsi}")
    except Exception as e:
        print(f"   ❌ Error calculating RSI: {e}")
        import traceback
        traceback.print_exc()
    
    # Test MACD
    try:
        from technicals.indicators import MACD
        df_macd = MACD(df, n_slow=26, n_fast=12, n_signal=9)
        print(f"   ✅ MACD calculated successfully")
        print(f"   📊 MACD columns: {[col for col in df_macd.columns if 'MACD' in col or 'SIGNAL' in col or 'HIST' in col]}")
    except Exception as e:
        print(f"   ❌ Error calculating MACD: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_technical_indicators()
