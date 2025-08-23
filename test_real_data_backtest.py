#!/usr/bin/env python3
"""
Test backtesting with real data and detailed signal analysis.
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


def load_real_data():
    """Load real historical data."""
    print("📊 Loading real historical data...")
    
    # Load EUR_USD M5 data
    file_path = "data/EUR_USD_M5.pkl"
    df = pd.read_pickle(file_path)
    
    # Take last 100 candles
    df_sample = df.tail(100)
    
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
    
    print(f"   ✅ Loaded {len(candles)} real candles")
    return candles


async def test_real_data_signals():
    """Test signal generation with real data."""
    print("🔧 Testing Signal Generation with Real Data...")
    
    # Load real data
    candles = load_real_data()
    
    # Initialize technical analyzer
    technical_analyzer = TechnicalAnalyzer()
    
    # Calculate indicators
    indicators = technical_analyzer.calculate_indicators(candles)
    print(f"   ✅ Technical indicators calculated")
    print(f"   📊 RSI: {indicators.rsi}")
    print(f"   📊 MACD: {indicators.macd}")
    print(f"   �� MACD Signal: {indicators.macd_signal}")
    print(f"   📊 Bollinger Upper: {indicators.bollinger_upper}")
    print(f"   📊 Bollinger Lower: {indicators.bollinger_lower}")
    print(f"   📊 Bollinger Middle: {indicators.bollinger_middle}")
    print(f"   📊 EMA Fast: {indicators.ema_fast}")
    print(f"   📊 EMA Slow: {indicators.ema_slow}")
    
    # Test signal generation with very lenient parameters
    from trading_bot.src.core.models import TradeSignal
    
    rsi_oversold = 45  # Very lenient
    rsi_overbought = 55  # Very lenient
    macd_signal_threshold = 0.000001  # Very sensitive
    bollinger_threshold = 0.005  # Very sensitive
    
    signals = {
        'rsi_signal': None,
        'macd_signal': None,
        'bollinger_signal': None,
        'ema_signal': None,
        'overall_signal': None,
        'has_signal': False,
        'signal_strength': 0.0,
        'reasoning': []
    }
    
    # RSI Analysis
    if indicators.rsi is not None:
        if indicators.rsi < rsi_oversold:
            signals['rsi_signal'] = TradeSignal.BUY
            signals['reasoning'].append(f"RSI oversold ({indicators.rsi:.2f})")
        elif indicators.rsi > rsi_overbought:
            signals['rsi_signal'] = TradeSignal.SELL
            signals['reasoning'].append(f"RSI overbought ({indicators.rsi:.2f})")
    
    # MACD Analysis
    if (indicators.macd is not None and indicators.macd_signal is not None and 
        abs(indicators.macd - indicators.macd_signal) > macd_signal_threshold):
        
        if indicators.macd > indicators.macd_signal:
            signals['macd_signal'] = TradeSignal.BUY
            signals['reasoning'].append("MACD bullish crossover")
        else:
            signals['macd_signal'] = TradeSignal.SELL
            signals['reasoning'].append("MACD bearish crossover")
    
    # Bollinger Bands Analysis
    if (indicators.bollinger_upper is not None and indicators.bollinger_lower is not None and 
        indicators.bollinger_middle is not None):
        
        # Calculate price position relative to bands
        price = indicators.bollinger_middle  # Use middle band as reference
        upper_distance = (indicators.bollinger_upper - price) / price
        lower_distance = (price - indicators.bollinger_lower) / price
        
        if upper_distance < bollinger_threshold:
            signals['bollinger_signal'] = TradeSignal.SELL
            signals['reasoning'].append("Price near upper Bollinger band")
        elif lower_distance < bollinger_threshold:
            signals['bollinger_signal'] = TradeSignal.BUY
            signals['reasoning'].append("Price near lower Bollinger band")
    
    # EMA Analysis
    if (indicators.ema_fast is not None and indicators.ema_slow is not None):
        if indicators.ema_fast > indicators.ema_slow:
            signals['ema_signal'] = TradeSignal.BUY
            signals['reasoning'].append("Fast EMA above slow EMA")
        else:
            signals['ema_signal'] = TradeSignal.SELL
            signals['reasoning'].append("Fast EMA below slow EMA")
    
    # Determine overall signal (very lenient: only need 1 signal)
    buy_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                     signals['bollinger_signal'], signals['ema_signal']] 
                    if signal == TradeSignal.BUY)
    sell_signals = sum(1 for signal in [signals['rsi_signal'], signals['macd_signal'], 
                                      signals['bollinger_signal'], signals['ema_signal']] 
                     if signal == TradeSignal.SELL)
    
    print(f"   📊 Individual signals:")
    print(f"      RSI: {signals['rsi_signal']}")
    print(f"      MACD: {signals['macd_signal']}")
    print(f"      Bollinger: {signals['bollinger_signal']}")
    print(f"      EMA: {signals['ema_signal']}")
    print(f"   📊 Buy signals: {buy_signals}")
    print(f"   📊 Sell signals: {sell_signals}")
    print(f"   📊 Reasoning: {signals['reasoning']}")
    
    if buy_signals > sell_signals and buy_signals >= 1:
        signals['overall_signal'] = TradeSignal.BUY
        signals['has_signal'] = True
        signals['signal_strength'] = buy_signals / 4.0
        print(f"   ✅ BUY signal generated with strength {signals['signal_strength']:.2f}")
    elif sell_signals > buy_signals and sell_signals >= 1:
        signals['overall_signal'] = TradeSignal.SELL
        signals['has_signal'] = True
        signals['signal_strength'] = sell_signals / 4.0
        print(f"   ✅ SELL signal generated with strength {signals['signal_strength']:.2f}")
    else:
        print(f"   ❌ No signal generated")


async def main():
    """Main function."""
    try:
        await test_real_data_signals()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
