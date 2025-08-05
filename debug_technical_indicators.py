#!/usr/bin/env python3
"""
Debug script to test technical indicator calculation.
"""

import asyncio
import sys
from pathlib import Path

# Add the market_adaptive_bot directory to the path
sys.path.append(str(Path(__file__).parent / "market_adaptive_bot" / "src"))

from core.models import CandleData, TimeFrame
from data.data_layer import DataLayer
from ai.technical_analyzer import TechnicalAnalyzer
from utils.config import Config
import pandas as pd

async def debug_technical_indicators():
    """Debug technical indicator calculation."""
    print("🔍 Debugging Technical Indicators")
    print("=" * 50)
    
    # Create config and data layer
    config = Config()
    data_layer = DataLayer(config)
    
    # Start data layer
    await data_layer.start()
    
    # Get candles
    candles = await data_layer.get_candles("EUR_USD", TimeFrame.M5, 50)
    print(f"✅ Got {len(candles)} candles")
    
    if len(candles) > 0:
        print(f"📊 Sample candle data:")
        print(f"   First candle: O={candles[0].open}, H={candles[0].high}, L={candles[0].low}, C={candles[0].close}")
        print(f"   Last candle: O={candles[-1].open}, H={candles[-1].high}, L={candles[-1].low}, C={candles[-1].close}")
    
    # Test technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    if len(candles) >= 20:
        print(f"\n🔧 Testing technical indicator calculation...")
        
        try:
            # Test DataFrame conversion
            df = technical_analyzer._candles_to_dataframe(candles)
            print(f"✅ DataFrame created with shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Sample data:")
            print(f"   {df.head(3)}")
            
            # Test RSI calculation
            from technicals.indicators import RSI
            df_rsi = RSI(df, n=14)
            print(f"\n📈 RSI calculation:")
            print(f"   RSI column exists: {'RSI_14' in df_rsi.columns}")
            if 'RSI_14' in df_rsi.columns:
                latest_rsi = df_rsi.iloc[-1]['RSI_14']
                print(f"   Latest RSI: {latest_rsi}")
                print(f"   Is NaN: {pd.isna(latest_rsi)}")
            
            # Test MACD calculation
            from technicals.indicators import MACD
            df_macd = MACD(df, n_slow=26, n_fast=12, n_signal=9)
            print(f"\n📊 MACD calculation:")
            print(f"   MACD columns: {[col for col in df_macd.columns if 'MACD' in col or 'SIGNAL' in col or 'HIST' in col]}")
            if 'MACD' in df_macd.columns:
                latest_macd = df_macd.iloc[-1]['MACD']
                print(f"   Latest MACD: {latest_macd}")
            
            # Test full indicator calculation
            indicators = technical_analyzer.calculate_indicators(candles)
            print(f"\n🎯 Full Technical Indicators:")
            print(f"   RSI (14): {indicators.rsi_14}")
            print(f"   MACD Line: {indicators.macd_line}")
            print(f"   MACD Signal: {indicators.macd_signal_line}")
            print(f"   Bollinger Upper: {indicators.bollinger_upper}")
            print(f"   Bollinger Lower: {indicators.bollinger_lower}")
            print(f"   ATR (14): {indicators.atr}")
            
        except Exception as e:
            print(f"❌ Error in technical calculation: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ Not enough candles for technical analysis")
    
    # Stop data layer
    await data_layer.stop()

if __name__ == "__main__":
    asyncio.run(debug_technical_indicators()) 