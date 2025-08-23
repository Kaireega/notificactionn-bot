#!/usr/bin/env python3
"""
Detailed debug script to test backtesting components step by step.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
import pandas as pd
import numpy as np

# Add the project root to the path for imports
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import TimeFrame, CandleData, MarketContext, MarketCondition
from trading_bot.src.ai.technical_analyzer import TechnicalAnalyzer


def load_sample_data() -> Dict[str, Dict[TimeFrame, List[CandleData]]]:
    """Load a small sample of historical data for debugging."""
    
    print("📊 Loading sample data for debugging...")
    
    # Load just EUR_USD M5 data for a short period
    file_path = "data/EUR_USD_M5.pkl"
    df = pd.read_pickle(file_path)
    
    # Take last 100 candles
    df_sample = df.tail(100)
    
    print(f"   📊 Original data shape: {df.shape}")
    print(f"   📊 Sample data shape: {df_sample.shape}")
    print(f"   📊 Sample data columns: {df_sample.columns.tolist()}")
    print(f"   📊 Sample data types:")
    for col in df_sample.columns:
        print(f"      {col}: {df_sample[col].dtype}")
    
    # Check for NaN values
    nan_counts = df_sample.isnull().sum()
    print(f"   📊 NaN counts:")
    for col, count in nan_counts.items():
        if count > 0:
            print(f"      {col}: {count}")
    
    # Convert to CandleData objects
    candles = []
    for idx, row in df_sample.iterrows():
        try:
            candle = CandleData(
                timestamp=row["time"].to_pydatetime(),
                open=Decimal(str(row["mid_o"])),
                high=Decimal(str(row["mid_h"])),
                low=Decimal(str(row["mid_l"])),
                close=Decimal(str(row["mid_c"])),
                volume=Decimal(str(row.get("volume", 1000)))
            )
            candles.append(candle)
        except Exception as e:
            print(f"   ❌ Error converting row {idx}: {e}")
            print(f"      Row data: {row.to_dict()}")
    
    print(f"   ✅ Converted {len(candles)} candles successfully")
    
    # Create historical data structure
    historical_data = {
        "EUR_USD": {
            TimeFrame.M5: candles
        }
    }
    
    return historical_data


def test_technical_analyzer():
    """Test the technical analyzer directly."""
    
    print("🔧 Testing Technical Analyzer...")
    
    # Initialize technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    # Load sample data
    historical_data = load_sample_data()
    
    # Test with one pair
    pair = "EUR_USD"
    timeframes = historical_data[pair]
    candles = timeframes[TimeFrame.M5]
    
    print(f"📊 Testing technical analyzer for {pair}...")
    print(f"   📊 Candles: {len(candles)}")
    
    # Test candles to DataFrame conversion
    try:
        df = technical_analyzer._candles_to_dataframe(candles)
        print(f"   ✅ DataFrame conversion successful")
        print(f"   📊 DataFrame shape: {df.shape}")
        print(f"   📊 DataFrame columns: {df.columns.tolist()}")
        print(f"   📊 DataFrame types:")
        for col in df.columns:
            print(f"      {col}: {df[col].dtype}")
        
        # Check for NaN values in DataFrame
        nan_counts = df.isnull().sum()
        print(f"   📊 DataFrame NaN counts:")
        for col, count in nan_counts.items():
            if count > 0:
                print(f"      {col}: {count}")
        
        # Show first few rows
        print(f"   📊 First few rows:")
        print(df.head())
        
    except Exception as e:
        print(f"   ❌ Error in DataFrame conversion: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test technical indicators calculation
    try:
        indicators = technical_analyzer.calculate_indicators(candles)
        print(f"   ✅ Technical indicators calculated successfully")
        print(f"   📊 RSI: {indicators.rsi}")
        print(f"   📊 MACD: {indicators.macd}")
        print(f"   📊 ATR: {indicators.atr}")
        
    except Exception as e:
        print(f"   ❌ Error calculating technical indicators: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    try:
        test_technical_analyzer()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
